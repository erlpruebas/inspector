from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from .base_engine import Engine
from .codex_engine import CodexEngine
from .command_engine import CommandEngine
from .opencode_engine import OpenCodeEngine


ROOT = Path(__file__).resolve().parents[1]


def create_engine(name: str) -> Engine:
    spec = parse_engine_spec(name)
    normalized = spec.provider
    if normalized == "codex":
        return CodexEngine(model=spec.model, name=spec.label)
    if normalized in {"groq", "openrouter", "lmstudio", "vikingnano"}:
        script = ROOT / "engines" / "api_wrapper.py"
        provider = normalized
        model_part = f"--model {_quote(spec.model)} " if spec.model else ""
        base_url = os.getenv("BENCH_LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1/chat/completions")
        base_part = f"--base-url {_quote(base_url)} " if normalized == "lmstudio" else ""
        if normalized == "vikingnano":
            base_url = os.getenv(
                "BENCH_VIKING_NANO_BASE_URL",
                "https://viking-occasion-married-dimensional.trycloudflare.com/v1/chat/completions",
            )
            base_part = f"--base-url {_quote(base_url)} "
        max_tokens = os.getenv("BENCH_LMSTUDIO_MAX_TOKENS", "256") if normalized == "lmstudio" else "2048"
        if normalized == "vikingnano":
            max_tokens = os.getenv("BENCH_VIKING_NANO_MAX_TOKENS", "2048")
        if normalized == "openrouter":
            max_tokens = os.getenv("BENCH_OPENROUTER_MAX_TOKENS", "384")
        api_timeout = os.getenv("BENCH_LMSTUDIO_API_TIMEOUT", "300") if normalized == "lmstudio" else "120"
        if normalized == "vikingnano":
            api_timeout = os.getenv("BENCH_VIKING_NANO_API_TIMEOUT", "600")
        context_mode = os.getenv("BENCH_LMSTUDIO_CONTEXT_MODE", "compact") if normalized == "lmstudio" else "full"
        command_timeout = int(os.getenv("BENCH_VIKING_NANO_COMMAND_TIMEOUT_SECONDS", "600")) if normalized == "vikingnano" else 1800
        command = (
            f'"{sys.executable}" "{script}" '
            f"--provider {provider} {model_part}{base_part}--prompt-file {{prompt_path}} --output {{output}} "
            f"--max-tokens {max_tokens} --timeout {api_timeout} --context-mode {context_mode}"
        )
        return CommandEngine(spec.label, command, model=spec.model, inject_workspace=False, timeout_seconds=command_timeout)
    if normalized in {"gemini_api", "gemini-api"}:
        script = ROOT / "engines" / "gemini_api_wrapper.py"
        model = spec.model or os.getenv("BENCH_GEMINI_API_MODEL", "gemini-2.5-flash-lite")
        command = f'"{sys.executable}" "{script}" --model {_quote(model)} --prompt-file {{prompt_path}} --output {{output}}'
        return CommandEngine(spec.label, command, model=model, inject_workspace=False)
    if normalized in {"chrome-nano", "chrome_nano"}:
        script = ROOT / "engines" / "chrome_nano_cli.py"
        model = spec.model or os.getenv("BENCH_CHROME_NANO_MODEL", "gemini-nano")
        timeout = os.getenv("BENCH_CHROME_NANO_TIMEOUT_SECONDS", "180")
        command = f'"{sys.executable}" "{script}" --model {_quote(model)} --prompt-file {{prompt_path}} --output {{output}} --timeout {timeout}'
        return CommandEngine(spec.label, command, model=model, inject_workspace=True)
    if normalized == "gemini":
        model = spec.model or os.getenv("BENCH_GEMINI_CLI_MODEL", "gemini-2.5-flash-lite")
        template = os.getenv(
            "BENCH_GEMINI_COMMAND_TEMPLATE",
            f"{_node_cli('gemini')} --skip-trust --approval-mode yolo --model {_quote(model)} -p \"\"",
        )
        timeout = int(os.getenv("BENCH_GEMINI_CLI_TIMEOUT_SECONDS", "420"))
        return CommandEngine(spec.label, template, model=model, timeout_seconds=timeout, stdin_prompt=True)
    if normalized == "opencode":
        model = spec.model or os.getenv("BENCH_OPENCODE_MODEL", "openrouter/deepseek/deepseek-v3.2")
        agent = os.getenv("BENCH_OPENCODE_AGENT", "build")
        return OpenCodeEngine(model=model, agent=agent, name=spec.label)
    if normalized == "command":
        template = os.getenv("BENCH_COMMAND_TEMPLATE", "").strip()
        if not template:
            raise ValueError("BENCH_COMMAND_TEMPLATE is required for the command engine")
        return CommandEngine(spec.label, template, model=spec.model)
    raise ValueError(f"Unknown benchmark engine: {name}")


class EngineSpec:
    def __init__(self, provider: str, model: str = "") -> None:
        self.provider = provider.lower().strip()
        self.model = model.strip()
        self.label = safe_label(self.provider if not self.model else f"{self.provider}_{self.model}")


def parse_engine_spec(value: str) -> EngineSpec:
    raw = value.strip()
    if "=" in raw:
        provider, model = raw.split("=", 1)
        return EngineSpec(provider, model)
    if ":" in raw:
        provider, model = raw.split(":", 1)
        return EngineSpec(provider, model)
    return EngineSpec(raw)


def safe_label(value: str) -> str:
    cleaned = []
    for char in value.lower():
        cleaned.append(char if char.isalnum() else "_")
    label = "".join(cleaned).strip("_")
    while "__" in label:
        label = label.replace("__", "_")
    return label or "engine"


def _quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def _cli(name: str) -> str:
    if os.name == "nt":
        path = shutil.which(f"{name}.cmd") or shutil.which(name)
    else:
        path = shutil.which(name)
    return f'"{path}"' if path else name


def _node_cli(name: str) -> str:
    if os.name != "nt":
        return _cli(name)
    appdata = os.getenv("APPDATA", "")
    node = shutil.which("node.exe") or "C:/Program Files/nodejs/node.exe"
    scripts = {
        "gemini": Path(appdata) / "npm" / "node_modules" / "@google" / "gemini-cli" / "bundle" / "gemini.js",
        "opencode": Path(appdata) / "npm" / "node_modules" / "opencode-ai" / "bin" / "opencode",
    }
    script = scripts.get(name)
    if script and script.exists():
        return f'"{node}" "{script}"'
    return _cli(name)
