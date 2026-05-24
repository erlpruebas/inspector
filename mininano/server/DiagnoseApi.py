from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
LOG_FILE = ROOT / "cloudflared.log"
DEFAULT_MODEL = "gemini-nano-local"


def find_latest_tunnel_url() -> str | None:
    if not LOG_FILE.exists():
        return None
    text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
    return matches[-1] if matches else None


def normalize_base_url(raw: str) -> str:
    raw = raw.strip().rstrip("/")
    if not raw:
        raw = "http://127.0.0.1:8788/v1"

    parsed = urllib.parse.urlparse(raw)
    if parsed.path in {"", "/"}:
        return raw + "/v1"
    if parsed.path == "/chat":
        return urllib.parse.urlunparse(parsed._replace(path="/v1", query="", fragment=""))
    if parsed.path.endswith("/v1"):
        return raw
    return raw + "/v1"


def origin_from_base(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "", "", "", ""))


def request_json(
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> tuple[int, dict[str, Any] | str]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            try:
                return response.status, json.loads(body)
            except json.JSONDecodeError:
                return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, body


def request_stream(base_url: str, api_key: str, model: str, timeout: float) -> str:
    payload = {
        "model": model,
        "stream": True,
        "messages": [{"role": "user", "content": "Responde solo: OK stream"}],
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Accept": "text/event-stream",
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        f"{base_url}/chat/completions", data=data, headers=headers, method="POST"
    )
    pieces: list[str] = []
    started = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as response:
        for raw_line in response:
            if time.time() - started > timeout:
                break
            line = raw_line.decode("utf-8", errors="replace").strip()
            if not line.startswith("data: "):
                continue
            value = line[6:]
            if value == "[DONE]":
                return "".join(pieces).strip()
            try:
                event = json.loads(value)
            except json.JSONDecodeError:
                continue
            choice = (event.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}
            if "content" in delta:
                pieces.append(str(delta["content"]))
    return "".join(pieces).strip()


def ok(label: str, message: str) -> None:
    print(f"[OK] {label}: {message}")


def fail(label: str, message: str) -> None:
    print(f"[ERROR] {label}: {message}")


def info(label: str, message: str) -> None:
    print(f"[INFO] {label}: {message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostico Mini Nano OpenAI-compatible")
    parser.add_argument("--base-url", default="", help="Ejemplo: https://xxx.trycloudflare.com/v1")
    parser.add_argument("--api-key", default="local", help="Clave API. Si no hay clave real, usa local.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--stream", action="store_true", help="Prueba tambien streaming SSE")
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()

    detected = find_latest_tunnel_url()
    raw_base = args.base_url or (detected + "/v1" if detected else "http://127.0.0.1:8788/v1")
    base_url = normalize_base_url(raw_base)
    origin = origin_from_base(base_url)
    parsed = urllib.parse.urlparse(base_url)

    print("Mini Nano API diagnostic")
    print()
    info("Base URL", base_url)
    info("Chat humano", origin + "/chat")
    info("Modelo", args.model)
    print()

    exit_code = 0

    try:
        addresses = socket.gethostbyname_ex(parsed.hostname or "")[2]
        ok("DNS", ", ".join(addresses))
    except Exception as exc:
        fail("DNS", str(exc))
        print()
        print("Esto suele significar URL vieja, tunel cerrado o DNS local bloqueando trycloudflare.")
        print("Prueba: Tunnel.bat, luego FixCurrentTunnelHosts.bat, o usa http://127.0.0.1:8788/v1 en esta maquina.")
        return 2

    try:
        status, health = request_json("GET", origin + "/health", args.api_key, timeout=10)
        if status == 200 and isinstance(health, dict) and health.get("ok"):
            ok("GET /health", json.dumps(health, ensure_ascii=False))
            if not health.get("browser_alive"):
                fail("Bridge Chrome", "el servidor esta vivo, pero la pestana bridge no parece conectada")
                exit_code = 3
        else:
            fail("GET /health", f"HTTP {status}: {health}")
            exit_code = 3
    except Exception as exc:
        fail("GET /health", str(exc))
        exit_code = 3

    try:
        status, models = request_json("GET", base_url + "/models", args.api_key, timeout=10)
        if status == 200:
            ids = []
            if isinstance(models, dict):
                ids = [str(item.get("id")) for item in models.get("data", [])]
            ok("GET /v1/models", ", ".join(ids) or "respuesta recibida")
        else:
            fail("GET /v1/models", f"HTTP {status}: {models}")
            exit_code = 4
    except Exception as exc:
        fail("GET /v1/models", str(exc))
        exit_code = 4

    payload = {
        "model": args.model,
        "stream": False,
        "messages": [{"role": "user", "content": "Responde solo: OK API"}],
    }
    try:
        status, completion = request_json(
            "POST", base_url + "/chat/completions", args.api_key, payload, timeout=args.timeout
        )
        if status == 200 and isinstance(completion, dict):
            content = (
                ((completion.get("choices") or [{}])[0].get("message") or {}).get("content")
                or ""
            )
            ok("POST /v1/chat/completions", content.strip() or "respuesta vacia")
        else:
            fail("POST /v1/chat/completions", f"HTTP {status}: {completion}")
            exit_code = 5
    except Exception as exc:
        fail("POST /v1/chat/completions", str(exc))
        exit_code = 5

    if args.stream:
        try:
            content = request_stream(base_url, args.api_key, args.model, args.timeout)
            ok("stream", content or "stream abierto, sin texto capturado")
        except Exception as exc:
            fail("stream", str(exc))
            exit_code = 6

    print()
    print("Configuracion correcta para clientes OpenAI-compatible:")
    print(f"  Base URL: {base_url}")
    print(f"  Model:    {args.model}")
    print(f"  API key:  {args.api_key or '(vacia si tu cliente lo permite)'}")
    print()
    print("Curl minimo:")
    print(
        "  curl -X POST "
        + f"\"{base_url}/chat/completions\" "
        + "-H \"Content-Type: application/json\" "
        + f"-H \"Authorization: Bearer {args.api_key or 'local'}\" "
        + "-d \"{\\\"model\\\":\\\""
        + args.model
        + "\\\",\\\"messages\\\":[{\\\"role\\\":\\\"user\\\",\\\"content\\\":\\\"di hola\\\"}]}\""
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
