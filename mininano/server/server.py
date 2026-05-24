from __future__ import annotations

import argparse
import json
import os
import queue
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parent
DEFAULT_BIND_HOST = "0.0.0.0"
LOCAL_HOST = "127.0.0.1"
PORT = 8788
DEFAULT_MODEL = "gemini-nano-local"
API_KEY = ""


def json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def now_ts() -> int:
    return int(time.time())


def normalize_content(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for message in messages:
        role = (message.get("role") or "user").strip().lower()
        content = str(message.get("content") or "")
        if role == "system":
            parts.append(f"System: {content}")
        elif role == "assistant":
            parts.append(f"Assistant: {content}")
        else:
            parts.append(f"User: {content}")
    return "\n".join(parts)


def build_prompt(messages: list[dict[str, Any]]) -> str:
    system_prompt = "Eres un asistente util y conciso. Responde siempre en espanol."
    lines = [system_prompt, "", "Conversation:"]
    lines.extend(normalize_content(messages).splitlines())
    lines.append("")
    lines.append("Assistant:")
    return "\n".join(lines)


@dataclass
class BridgeJob:
    job_id: str
    payload: dict[str, Any]
    created_at: float = field(default_factory=time.time)
    events: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    done: bool = False
    error: str | None = None
    content: str = ""
    finished_at: float | None = None
    wake: threading.Event = field(default_factory=threading.Event)


class BridgeState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: "queue.Queue[str]" = queue.Queue()
        self._jobs: dict[str, BridgeJob] = {}
        self._browser_last_ping = 0.0
        self._current_job_id: str | None = None
        self.last_error: str | None = None

    def submit_job(self, payload: dict[str, Any]) -> BridgeJob:
        job = BridgeJob(job_id=uuid4().hex[:12], payload=payload)
        with self._lock:
            self._jobs[job.job_id] = job
        self._pending.put(job.job_id)
        return job

    def next_job(self) -> dict[str, Any] | None:
        try:
            job_id = self._pending.get_nowait()
        except queue.Empty:
            self._current_job_id = None
            return None

        with self._lock:
            job = self._jobs.get(job_id)
        self._current_job_id = job_id
        self._browser_last_ping = time.time()
        if not job:
            return None
        return {
            "id": job.job_id,
            "model": job.payload.get("model") or DEFAULT_MODEL,
            "messages": job.payload.get("messages") or [],
            "temperature": job.payload.get("temperature"),
            "top_p": job.payload.get("top_p"),
            "max_tokens": job.payload.get("max_tokens"),
        }

    def get_job(self, job_id: str) -> BridgeJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def browser_alive(self) -> bool:
        return (time.time() - self._browser_last_ping) < 8.0

    def ping_browser(self) -> None:
        self._browser_last_ping = time.time()

    def set_current_job(self, job_id: str | None) -> None:
        self._current_job_id = job_id

    def current_job(self) -> str | None:
        return self._current_job_id

    def push_event(self, job_id: str, event: dict[str, Any]) -> None:
        job = self.get_job(job_id)
        if not job:
            return

        job.events.put(event)
        event_type = event.get("type")
        if event_type == "delta":
            job.content = str(event.get("content") or (job.content + str(event.get("delta") or "")))
        elif event_type == "done":
            job.content = str(event.get("content") or job.content)
            job.done = True
            job.finished_at = time.time()
            job.wake.set()
        elif event_type == "error":
            job.error = str(event.get("error") or "unknown error")
            self.last_error = job.error
            job.done = True
            job.finished_at = time.time()
            job.wake.set()


STATE = BridgeState()


class MiniNanoServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, Accept, OpenAI-Organization, OpenAI-Project, X-API-Key",
        )

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _authorized(self) -> bool:
        if not API_KEY:
            return True
        auth = self.headers.get("Authorization") or ""
        bearer = auth.replace("Bearer ", "", 1).strip() if auth.lower().startswith("bearer ") else ""
        header_key = (self.headers.get("X-API-Key") or "").strip()
        return bearer == API_KEY or header_key == API_KEY

    def _send_auth_error(self) -> None:
        self._send_json(
            {
                "error": {
                    "message": "Missing or invalid Mini Nano API key",
                    "type": "authentication_error",
                }
            },
            status=401,
        )

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in {"/", "/chat", "/index.html"}:
            self.path = "/index.html"
            return super().do_GET()

        if path in {"/bridge", "/bridge.html"}:
            self.path = "/bridge.html"
            return super().do_GET()

        if path == "/health":
            self._send_json(
                {
                    "ok": True,
                    "browser_alive": STATE.browser_alive(),
                    "queue_size": STATE._pending.qsize(),
                    "current_job": STATE.current_job(),
                    "last_error": STATE.last_error,
                }
            )
            return

        if path == "/api/bridge/next":
            STATE.ping_browser()
            job = STATE.next_job()
            self._send_json({"job": job})
            return

        if path == "/api/bridge/status":
            self._send_json(
                {
                    "ok": True,
                    "browser_alive": STATE.browser_alive(),
                    "queue_size": STATE._pending.qsize(),
                    "current_job": STATE.current_job(),
                    "last_error": STATE.last_error,
                }
            )
            return

        if path == "/api/bridge/ping":
            STATE.ping_browser()
            self._send_json({"ok": True})
            return

        if path == "/config":
            self._send_json(
                {
                    "model": DEFAULT_MODEL,
                    "auth_required": bool(API_KEY),
                    "api_base_url": "",
                }
            )
            return

        if path == "/v1/models":
            if not self._authorized():
                self._send_auth_error()
                return
            self._send_json(
                {
                    "object": "list",
                    "data": [
                        {
                            "id": DEFAULT_MODEL,
                            "object": "model",
                            "created": now_ts(),
                            "owned_by": "local",
                        }
                    ],
                }
            )
            return

        super().do_GET()

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}

        if parsed.path == "/api/bridge/event":
            job_id = str(payload.get("job_id") or "")
            event = {k: v for k, v in payload.items() if k != "job_id"}
            STATE.push_event(job_id, event)
            self._send_json({"ok": True})
            return

        if parsed.path == "/api/bridge/ping":
            STATE.ping_browser()
            self._send_json({"ok": True})
            return

        if parsed.path == "/api/jobs/submit":
            job = STATE.submit_job(payload)
            self._send_json({"job_id": job.job_id})
            return

        if parsed.path == "/v1/chat/completions":
            if not self._authorized():
                self._send_auth_error()
                return
            self.handle_chat_completions(payload)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def handle_chat_completions(self, payload: dict[str, Any]) -> None:
        model = str(payload.get("model") or DEFAULT_MODEL)
        messages = payload.get("messages") or []
        if not isinstance(messages, list):
            self._send_json({"error": {"message": "`messages` must be a list"}}, status=400)
            return

        job = STATE.submit_job(
            {
                "model": model,
                "messages": messages,
                "temperature": payload.get("temperature"),
                "top_p": payload.get("top_p"),
                "max_tokens": payload.get("max_tokens"),
            }
        )

        stream = bool(payload.get("stream"))
        if stream:
            self._handle_stream_response(job)
        else:
            self._handle_blocking_response(job, model)

    def _wait_for_job(self, job: BridgeJob, timeout_s: float = 300.0) -> bool:
        return job.wake.wait(timeout_s)

    def _handle_blocking_response(self, job: BridgeJob, model: str) -> None:
        if not self._wait_for_job(job):
            self._send_json(
                {"error": {"message": "Timed out waiting for browser bridge"}}, status=504
            )
            return

        if job.error:
            self._send_json({"error": {"message": job.error}}, status=500)
            return

        response = {
            "id": f"chatcmpl-{job.job_id}",
            "object": "chat.completion",
            "created": now_ts(),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": job.content},
                    "finish_reason": "stop",
                }
            ],
        }
        self._send_json(response)

    def _sse_write(self, text: str) -> None:
        self.wfile.write(text.encode("utf-8"))
        self.wfile.flush()

    def _handle_stream_response(self, job: BridgeJob) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-transform")
        self.send_header("Connection", "keep-alive")
        self._cors()
        self.end_headers()

        def send_chunk(delta: dict[str, Any], finish_reason: str | None = None) -> None:
            payload = {
                "id": f"chatcmpl-{job.job_id}",
                "object": "chat.completion.chunk",
                "created": now_ts(),
                "model": job.payload.get("model") or DEFAULT_MODEL,
                "choices": [
                    {
                        "index": 0,
                        "delta": delta,
                        "finish_reason": finish_reason,
                    }
                ],
            }
            self._sse_write(f"data: {json.dumps(payload, ensure_ascii=False)}\n\n")

        send_chunk({"role": "assistant"})

        while True:
            try:
                event = job.events.get(timeout=0.5)
            except queue.Empty:
                if job.done:
                    break
                continue

            event_type = event.get("type")
            if event_type == "delta":
                delta_text = str(event.get("delta") or "")
                if delta_text:
                    send_chunk({"content": delta_text})
            elif event_type == "done":
                send_chunk({}, finish_reason="stop")
                self._sse_write("data: [DONE]\n\n")
                return
            elif event_type == "error":
                error_payload = {
                    "error": {
                        "message": str(event.get("error") or "unknown error"),
                    }
                }
                self._sse_write(f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n")
                self._sse_write("data: [DONE]\n\n")
                return

        send_chunk({}, finish_reason="stop")
        self._sse_write("data: [DONE]\n\n")


def open_bridge(mock: bool) -> None:
    url = f"http://{LOCAL_HOST}:{PORT}/bridge.html"
    if mock:
        url += "?mock=1"
    webbrowser.open(url)


def smoke_test() -> None:
    with urllib.request.urlopen(f"http://{LOCAL_HOST}:{PORT}/health", timeout=5) as response:
        assert response.status == 200
        payload = json.loads(response.read().decode("utf-8"))
        assert payload["ok"] is True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mini Nano local OpenAI-compatible server")
    parser.add_argument("--mock", action="store_true", help="open the bridge page in mock mode")
    parser.add_argument("--host", default=DEFAULT_BIND_HOST, help="bind host for remote access")
    parser.add_argument("--port", type=int, default=PORT, help="listen port")
    parser.add_argument("--api-key", default="", help="optional API key required by /v1 endpoints")
    parser.add_argument("--no-open", action="store_true", help="do not open the browser bridge")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bind_host = args.host
    global PORT, API_KEY
    PORT = args.port
    API_KEY = args.api_key or os.environ.get("MINI_NANO_API_KEY", "")

    server = ThreadingHTTPServer((bind_host, PORT), MiniNanoServer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    smoke_test()
    if not args.no_open:
        open_bridge(args.mock)

    print(f"Mini Nano server listening on http://{bind_host}:{PORT}")
    print(f"Bridge: http://{LOCAL_HOST}:{PORT}/bridge.html" + ("?mock=1" if args.mock else ""))
    print(f"API key required: {'yes' if API_KEY else 'no'}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
