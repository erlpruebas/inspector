from __future__ import annotations

import argparse
import json
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

try:
    from .chrome_nano_bridge import ChromeNanoBridge, ChromeNanoError, DEFAULT_MODEL, openai_messages_to_prompt
except ImportError:  # pragma: no cover - script execution fallback
    from chrome_nano_bridge import ChromeNanoBridge, ChromeNanoError, DEFAULT_MODEL, openai_messages_to_prompt


class ChromeNanoOpenAIServer:
    def __init__(self, host: str, port: int, bridge: ChromeNanoBridge | None = None) -> None:
        self.bridge = bridge or ChromeNanoBridge()
        self.httpd = HTTPServer((host, port), self._handler())

    def serve_forever(self) -> None:
        try:
            self.httpd.serve_forever()
        finally:
            self.bridge.close()

    def _handler(self):
        bridge = self.bridge

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def do_GET(self) -> None:
                if self.path == "/health":
                    self._send_json(HTTPStatus.OK, bridge.health())
                    return
                if self.path == "/v1/models":
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "object": "list",
                            "data": [
                                {
                                    "id": DEFAULT_MODEL,
                                    "object": "model",
                                    "created": 0,
                                    "owned_by": "chrome",
                                }
                            ],
                        },
                    )
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": {"message": "not found"}})

            def do_POST(self) -> None:
                if self.path.startswith("/v1/abort/"):
                    request_id = self.path.rsplit("/", 1)[-1]
                    aborted = bridge.abort_request(request_id)
                    self._send_json(
                        HTTPStatus.OK,
                        {"ok": True, "request_id": request_id, "aborted": aborted},
                    )
                    return
                if self.path == "/v1/chat/completions":
                    self._chat_completions()
                    return
                self._send_json(HTTPStatus.NOT_FOUND, {"error": {"message": "not found"}})

            def _chat_completions(self) -> None:
                request_id = uuid.uuid4().hex
                try:
                    body = self._read_json()
                    messages = body.get("messages") or []
                    prompt, system_prompt = openai_messages_to_prompt(messages)
                    stream = bool(body.get("stream"))
                    temperature = float(body.get("temperature", 0) or 0)
                    request_id = str(body.get("request_id") or request_id)
                    if stream:
                        self._send_sse_stream(
                            prompt=prompt,
                            system_prompt=system_prompt,
                            temperature=temperature,
                            request_id=request_id,
                            model=str(body.get("model") or DEFAULT_MODEL),
                        )
                        return
                    response = bridge.prompt(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        request_id=request_id,
                    )
                    now = int(time.time())
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "id": "chatcmpl-" + uuid.uuid4().hex,
                            "object": "chat.completion",
                            "created": now,
                            "model": body.get("model") or DEFAULT_MODEL,
                            "choices": [
                                {
                                    "index": 0,
                                    "message": {"role": "assistant", "content": response.content},
                                    "finish_reason": "stop",
                                }
                            ],
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0,
                                "note": "Chrome Prompt API does not expose token usage.",
                            },
                        },
                    )
                except ChromeNanoError as exc:
                    self._send_json(
                        HTTPStatus.SERVICE_UNAVAILABLE,
                        {
                            "error": {
                                "message": str(exc),
                                "type": "chrome_nano_unavailable",
                                "request_id": request_id,
                            }
                        },
                    )
                except json.JSONDecodeError as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": {"message": f"invalid JSON: {exc.msg}"}})
                except Exception as exc:
                    self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": {"message": f"{type(exc).__name__}: {exc}"}})

            def _read_json(self) -> dict[str, Any]:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length).decode("utf-8", errors="replace")
                data = json.loads(raw or "{}")
                return data if isinstance(data, dict) else {}

            def _send_json(self, status: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(int(status))
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(body)

            def _send_sse_stream(
                self,
                prompt: str,
                system_prompt: str,
                temperature: float,
                request_id: str,
                model: str,
            ) -> None:
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "close")
                self.end_headers()
                created = int(time.time())
                def write_chunk(chunk: str) -> None:
                    payload = {
                        "id": "chatcmpl-" + request_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": chunk},
                                "finish_reason": None,
                            }
                        ],
                    }
                    self.wfile.write(("data: " + json.dumps(payload, ensure_ascii=False) + "\n\n").encode("utf-8"))
                    self.wfile.flush()

                try:
                    bridge.prompt_stream_to_callback(
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        request_id=request_id,
                        on_chunk=write_chunk,
                    )
                    final_payload = {
                        "id": "chatcmpl-" + request_id,
                        "object": "chat.completion.chunk",
                        "created": created,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "finish_reason": "stop",
                            }
                        ],
                    }
                    self.wfile.write(("data: " + json.dumps(final_payload, ensure_ascii=False) + "\n\n").encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                except ChromeNanoError as exc:
                    error_payload = {"error": {"message": str(exc), "type": "chrome_nano_unavailable", "request_id": request_id}}
                    self.wfile.write(("data: " + json.dumps(error_payload, ensure_ascii=False) + "\n\n").encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                except BrokenPipeError:
                    bridge.abort_request(request_id)
                except Exception as exc:
                    error_payload = {"error": {"message": f"{type(exc).__name__}: {exc}", "request_id": request_id}}
                    self.wfile.write(("data: " + json.dumps(error_payload, ensure_ascii=False) + "\n\n").encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()

            def log_message(self, format: str, *args: Any) -> None:
                print(format % args)

        return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAI-compatible local server for Chrome Gemini Nano.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ChromeNanoOpenAIServer(args.host, args.port)
    print(f"Chrome Nano OpenAI-compatible server listening on http://{args.host}:{args.port}")
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
