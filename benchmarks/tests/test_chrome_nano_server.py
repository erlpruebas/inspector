from __future__ import annotations

import http.client
import json
import threading
import time
import unittest
from typing import Any

from benchmarks.engines.chrome_nano_bridge import ChromeNanoResponse, openai_messages_to_prompt
from benchmarks.engines.chrome_nano_server import ChromeNanoOpenAIServer


class FakeBridge:
    def __init__(self) -> None:
        self.aborted: list[str] = []
        self.closed = False

    def health(self) -> dict[str, Any]:
        return {"ok": True, "availability": "available", "model": "gemini-nano"}

    def prompt(self, prompt: str, system_prompt: str = "", temperature: float = 0.0, request_id: str | None = None) -> ChromeNanoResponse:
        return ChromeNanoResponse(
            content=f"{system_prompt}|{prompt}|{temperature}",
            availability="available",
            elapsed_seconds=0.01,
            request_id=request_id or "req",
        )

    def prompt_stream(self, prompt: str, system_prompt: str = "", temperature: float = 0.0, request_id: str | None = None):
        del system_prompt, temperature, request_id
        return iter([prompt[:3], prompt[3:]])

    def prompt_stream_to_callback(
        self,
        prompt: str,
        on_chunk,
        system_prompt: str = "",
        temperature: float = 0.0,
        request_id: str | None = None,
    ) -> None:
        del system_prompt, temperature, request_id
        on_chunk(prompt[:3])
        on_chunk(prompt[3:])

    def abort_request(self, request_id: str) -> bool:
        self.aborted.append(request_id)
        return True

    def close(self) -> None:
        self.closed = True


class ChromeNanoServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bridge = FakeBridge()
        cls.server = ChromeNanoOpenAIServer("127.0.0.1", 0, bridge=cls.bridge)
        cls.thread = threading.Thread(target=cls.server.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.httpd.server_port
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.httpd.shutdown()
        cls.server.httpd.server_close()
        cls.bridge.close()

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> tuple[int, str]:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if body is not None else {}
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        content = response.read().decode("utf-8")
        conn.close()
        return response.status, content

    def test_openai_messages_to_prompt(self) -> None:
        prompt, system_prompt = openai_messages_to_prompt(
            [
                {"role": "system", "content": "Be concise"},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi"},
            ]
        )
        self.assertEqual(system_prompt, "Be concise")
        self.assertIn("USER:\nHello", prompt)
        self.assertIn("ASSISTANT:\nHi", prompt)

    def test_health(self) -> None:
        status, content = self._request("GET", "/health")
        self.assertEqual(status, 200)
        data = json.loads(content)
        self.assertTrue(data["ok"])

    def test_models(self) -> None:
        status, content = self._request("GET", "/v1/models")
        self.assertEqual(status, 200)
        data = json.loads(content)
        self.assertEqual(data["data"][0]["id"], "gemini-nano")

    def test_chat_completions(self) -> None:
        status, content = self._request(
            "POST",
            "/v1/chat/completions",
            {
                "model": "gemini-nano",
                "messages": [{"role": "user", "content": "ping"}],
                "temperature": 0.2,
            },
        )
        self.assertEqual(status, 200)
        data = json.loads(content)
        self.assertEqual(data["choices"][0]["message"]["content"], "|USER:\nping|0.2")

    def test_streaming_chat_completions(self) -> None:
        status, content = self._request(
            "POST",
            "/v1/chat/completions",
            {
                "model": "gemini-nano",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
            },
        )
        self.assertEqual(status, 200)
        self.assertIn("data: ", content)
        self.assertIn("[DONE]", content)

    def test_abort(self) -> None:
        status, content = self._request("POST", "/v1/abort/request-123", {})
        self.assertEqual(status, 200)
        data = json.loads(content)
        self.assertTrue(data["aborted"])
        self.assertIn("request-123", self.bridge.aborted)


if __name__ == "__main__":
    unittest.main()
