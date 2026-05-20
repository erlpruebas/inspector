from __future__ import annotations

import json
import os
import shutil
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Iterator


DEFAULT_MODEL = "gemini-nano"
DEFAULT_TIMEOUT_SECONDS = 180


@dataclass
class ChromeNanoResponse:
    content: str
    availability: str
    elapsed_seconds: float
    request_id: str = ""


class ChromeNanoError(RuntimeError):
    pass


class ChromeNanoBridge:
    def __init__(
        self,
        headless: bool | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        chrome_path: str = "",
        user_data_dir: str = "",
    ) -> None:
        self.headless = _truthy(os.getenv("CHROME_NANO_HEADLESS", "false")) if headless is None else headless
        self.timeout_seconds = int(os.getenv("CHROME_NANO_TIMEOUT_SECONDS", str(timeout_seconds)))
        self.chrome_path = chrome_path or os.getenv("CHROME_NANO_CHROME_PATH", "") or find_chrome()
        self.user_data_dir = user_data_dir or os.getenv("CHROME_NANO_USER_DATA_DIR", "")
        self._lock = threading.RLock()
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        self._server: LocalPageServer | None = None
        self._abort_flags: dict[str, threading.Event] = {}
        self._stream_callbacks: dict[str, Callable[[str], None]] = {}

    def close(self) -> None:
        with self._lock:
            for event in self._abort_flags.values():
                event.set()
            self._abort_flags.clear()
            self._stream_callbacks.clear()
            for obj in (self._context, self._browser):
                if obj is not None:
                    try:
                        obj.close()
                    except Exception:
                        pass
            if self._playwright is not None:
                try:
                    self._playwright.stop()
                except Exception:
                    pass
            if self._server is not None:
                self._server.close()
            self._playwright = None
            self._browser = None
            self._context = None
            self._page = None
            self._server = None

    def health(self) -> dict[str, Any]:
        with self._lock:
            self._ensure_page()
            availability = self._availability_unlocked()
            return {
                "ok": availability in {"available", "readily", "downloadable", "downloading"},
                "availability": availability,
                "model": DEFAULT_MODEL,
                "chrome_path": self.chrome_path,
                "headless": self.headless,
            }

    def availability(self) -> str:
        with self._lock:
            self._ensure_page()
            return self._availability_unlocked()

    def abort_request(self, request_id: str) -> bool:
        with self._lock:
            flag = self._abort_flags.get(request_id)
        if flag is None:
            return False
        flag.set()
        return True

    def prompt(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        request_id: str | None = None,
    ) -> ChromeNanoResponse:
        started = time.monotonic()
        request_id = request_id or uuid.uuid4().hex
        with self._lock:
            self._ensure_page()
            availability = self._availability_unlocked()
            if availability not in {"available", "readily"}:
                raise ChromeNanoError(
                    f"Chrome Gemini Nano is not available: {availability}. "
                    "Enable Chrome Built-in AI flags and wait for the model download if needed."
                )
            self._register_abort_flag(request_id)
            payload = {
                "requestId": request_id,
                "prompt": prompt,
                "systemPrompt": system_prompt,
                "temperature": temperature,
                "timeoutMs": self.timeout_seconds * 1000,
            }
            result = self._page.evaluate(CHROME_PROMPT_SCRIPT, payload)
        try:
            if not isinstance(result, dict) or not result.get("ok"):
                detail = result.get("error") if isinstance(result, dict) else result
                raise ChromeNanoError(str(detail))
            return ChromeNanoResponse(
                content=str(result.get("content", "")).strip(),
                availability=availability,
                elapsed_seconds=round(time.monotonic() - started, 3),
                request_id=request_id,
            )
        finally:
            self._clear_request(request_id)

    def prompt_stream(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: float = 0.0,
        request_id: str | None = None,
    ) -> Iterator[str]:
        chunks: list[str] = []
        self.prompt_stream_to_callback(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            request_id=request_id,
            on_chunk=chunks.append,
        )
        return iter(chunks)

    def prompt_stream_to_callback(
        self,
        prompt: str,
        on_chunk: Callable[[str], None],
        system_prompt: str = "",
        temperature: float = 0.0,
        request_id: str | None = None,
    ) -> None:
        request_id = request_id or uuid.uuid4().hex
        with self._lock:
            self._ensure_page()
            availability = self._availability_unlocked()
            if availability not in {"available", "readily"}:
                raise ChromeNanoError(
                    f"Chrome Gemini Nano is not available: {availability}. "
                    "Enable Chrome Built-in AI flags and wait for the model download if needed."
                )
            self._register_abort_flag(request_id)
            self._stream_callbacks[request_id] = on_chunk
            payload = {
                "requestId": request_id,
                "prompt": prompt,
                "systemPrompt": system_prompt,
                "temperature": temperature,
                "timeoutMs": self.timeout_seconds * 1000,
            }
            try:
                result = self._page.evaluate(CHROME_PROMPT_STREAM_SCRIPT, payload)
            finally:
                self._clear_request(request_id)
        if not isinstance(result, dict) or not result.get("ok"):
            detail = result.get("error") if isinstance(result, dict) else result
            raise ChromeNanoError(str(detail))

    def _register_abort_flag(self, request_id: str) -> None:
        with self._lock:
            self._abort_flags[request_id] = threading.Event()

    def _clear_request(self, request_id: str) -> None:
        with self._lock:
            self._abort_flags.pop(request_id, None)
            self._stream_callbacks.pop(request_id, None)

    def _is_aborted(self, request_id: str) -> bool:
        with self._lock:
            event = self._abort_flags.get(request_id)
        return bool(event and event.is_set())

    def _push_stream_chunk(self, request_id: str, chunk: Any) -> None:
        text = str(chunk or "")
        if not text:
            return
        with self._lock:
            callback = self._stream_callbacks.get(request_id)
        if callback is not None:
            callback(text)

    def _ensure_page(self) -> None:
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise ChromeNanoError("Missing Python package 'playwright'. Install with: python -m pip install playwright") from exc
        if not self.chrome_path:
            raise ChromeNanoError("Chrome executable not found. Set CHROME_NANO_CHROME_PATH.")

        try:
            self._server = LocalPageServer()
            self._server.start()
            self._playwright = sync_playwright().start()
            launch_args = chrome_flags()
            if self.user_data_dir:
                self._context = self._playwright.chromium.launch_persistent_context(
                    self.user_data_dir,
                    executable_path=self.chrome_path,
                    headless=self.headless,
                    args=launch_args,
                )
                self._page = self._context.new_page()
            else:
                self._browser = self._playwright.chromium.launch(
                    executable_path=self.chrome_path,
                    headless=self.headless,
                    args=launch_args,
                )
                self._context = self._browser.new_context()
                self._page = self._context.new_page()
            self._page.expose_function("__chromeNanoStreamChunk", self._push_stream_chunk)
            self._page.expose_function("__chromeNanoShouldAbort", self._is_aborted)
            self._page.goto(self._server.url, wait_until="domcontentloaded", timeout=30_000)
            self._page.evaluate(CHROME_SETUP_SCRIPT)
        except Exception as exc:
            self.close()
            raise ChromeNanoError(f"Failed to launch Chrome Nano bridge: {type(exc).__name__}: {exc}") from exc

    def _availability_unlocked(self) -> str:
        result = self._page.evaluate(CHROME_AVAILABILITY_SCRIPT)
        if isinstance(result, dict) and result.get("ok"):
            return str(result.get("availability", "unknown"))
        if isinstance(result, dict):
            return "error: " + str(result.get("error", "unknown"))
        return "unknown"


class LocalPageServer:
    def __init__(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="chrome-nano-page-"))
        (self.directory / "index.html").write_text(
            "<!doctype html><meta charset='utf-8'><title>Chrome Nano Bridge</title><body>ready</body>",
            encoding="utf-8",
        )
        (self.directory / "favicon.ico").write_bytes(b"")
        handler = self._handler()
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/index.html"

    def start(self) -> None:
        self.thread.start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.directory, ignore_errors=True)

    def _handler(self):
        directory = str(self.directory)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

            def log_message(self, format: str, *args: Any) -> None:
                return

        return Handler


def openai_messages_to_prompt(messages: list[dict[str, Any]]) -> tuple[str, str]:
    system_parts: list[str] = []
    body_parts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = str(message.get("role", "user"))
        content = _content_text(message.get("content", ""))
        if role == "system":
            system_parts.append(content)
        elif role == "assistant":
            body_parts.append(f"ASSISTANT:\n{content}")
        else:
            body_parts.append(f"{role.upper()}:\n{content}")
    return "\n\n".join(body_parts).strip(), "\n\n".join(system_parts).strip()


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif "text" in item:
                    parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part)
    return str(content)


def find_chrome() -> str:
    candidates = [
        os.getenv("CHROME_PATH", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    for name in ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return ""


def chrome_flags() -> list[str]:
    raw = os.getenv(
        "CHROME_NANO_FLAGS",
        "--enable-features=PromptAPIForGeminiNano,OptimizationGuideOnDeviceModel",
    )
    return [item for item in raw.split() if item]


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


CHROME_AVAILABILITY_SCRIPT = """
async () => {
  try {
    const lm = globalThis.LanguageModel || globalThis.ai?.languageModel;
    if (!lm) return {ok: false, error: "LanguageModel API not found"};
    const availability = await lm.availability(globalThis.__chromeNanoModelOptions());
    return {ok: true, availability};
  } catch (error) {
    return {ok: false, error: String(error && error.message || error)};
  }
}
"""


CHROME_PROMPT_SCRIPT = """
async (payload) => {
  try {
    const lm = globalThis.LanguageModel || globalThis.ai?.languageModel;
    if (!lm) return {ok: false, error: "LanguageModel API not found"};
    const availability = await lm.availability(globalThis.__chromeNanoModelOptions());
    if (availability !== "available" && availability !== "readily") {
      return {ok: false, error: "LanguageModel availability: " + availability};
    }
    const session = await window.__chromeNanoEnsureSession({
      systemPrompt: payload.systemPrompt,
      temperature: payload.temperature,
    });
    const controller = new AbortController();
    const timer = setInterval(async () => {
      try {
        if (await window.__chromeNanoShouldAbort(payload.requestId)) {
          controller.abort("aborted");
        }
      } catch (error) {
        controller.abort(String(error && error.message || error));
      }
    }, 100);
    try {
      const content = await session.prompt(payload.prompt, {signal: controller.signal});
      return {ok: true, content};
    } finally {
      clearInterval(timer);
    }
  } catch (error) {
    return {ok: false, error: String(error && error.message || error)};
  }
}
"""


CHROME_PROMPT_STREAM_SCRIPT = """
async (payload) => {
  try {
    const lm = globalThis.LanguageModel || globalThis.ai?.languageModel;
    if (!lm) return {ok: false, error: "LanguageModel API not found"};
    const availability = await lm.availability(globalThis.__chromeNanoModelOptions());
    if (availability !== "available" && availability !== "readily") {
      return {ok: false, error: "LanguageModel availability: " + availability};
    }
    const session = await window.__chromeNanoEnsureSession({
      systemPrompt: payload.systemPrompt,
      temperature: payload.temperature,
    });
    const controller = new AbortController();
    const timer = setInterval(async () => {
      try {
        if (await window.__chromeNanoShouldAbort(payload.requestId)) {
          controller.abort("aborted");
        }
      } catch (error) {
        controller.abort(String(error && error.message || error));
      }
    }, 100);
    try {
      const stream = session.promptStreaming(payload.prompt, {signal: controller.signal});
      let content = "";
      for await (const chunk of stream) {
        const text = String(chunk ?? "");
        content += text;
        await window.__chromeNanoStreamChunk(payload.requestId, text);
        if (await window.__chromeNanoShouldAbort(payload.requestId)) {
          controller.abort("aborted");
          break;
        }
      }
      return {ok: true, content};
    } finally {
      clearInterval(timer);
    }
  } catch (error) {
    return {ok: false, error: String(error && error.message || error)};
  }
}
"""


CHROME_SETUP_SCRIPT = """
() => {
  globalThis.__chromeNanoSession = null;
  globalThis.__chromeNanoSessionConfig = null;
  globalThis.__chromeNanoModelOptions = () => ({
    expectedInputs: [{type: "text", languages: ["es", "en"]}],
    expectedOutputs: [{type: "text", languages: ["es", "en"]}],
  });
  globalThis.__chromeNanoEnsureSession = async (config) => {
    const nextConfig = {
      systemPrompt: config?.systemPrompt || "",
      temperature: Number.isFinite(config?.temperature) ? config.temperature : 0,
    };
    const sameSession =
      globalThis.__chromeNanoSession &&
      globalThis.__chromeNanoSessionConfig &&
      globalThis.__chromeNanoSessionConfig.systemPrompt === nextConfig.systemPrompt &&
      globalThis.__chromeNanoSessionConfig.temperature === nextConfig.temperature;
    if (sameSession) {
      return globalThis.__chromeNanoSession;
    }
    if (globalThis.__chromeNanoSession && globalThis.__chromeNanoSession.destroy) {
      try {
        globalThis.__chromeNanoSession.destroy();
      } catch (error) {
        void error;
      }
    }
    const options = {};
    Object.assign(options, globalThis.__chromeNanoModelOptions());
    if (nextConfig.systemPrompt) options.systemPrompt = nextConfig.systemPrompt;
    if (Number.isFinite(nextConfig.temperature)) options.temperature = nextConfig.temperature;
    globalThis.__chromeNanoSession = await (globalThis.LanguageModel || globalThis.ai?.languageModel).create(options);
    globalThis.__chromeNanoSessionConfig = nextConfig;
    return globalThis.__chromeNanoSession;
  };
}
"""
