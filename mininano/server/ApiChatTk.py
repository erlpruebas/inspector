from __future__ import annotations

import json
import http.client
import queue
import re
import ssl
import socket
import threading
import tkinter as tk
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


DEFAULT_BASE_URL = "http://127.0.0.1:8788/v1"
DEFAULT_MODEL = "gemini-nano-local"
LOG_FILE = Path(__file__).resolve().parent / "cloudflared.log"


def find_latest_tunnel_url() -> str | None:
    if not LOG_FILE.exists():
        return None
    text = LOG_FILE.read_text(encoding="utf-8", errors="replace")
    matches = re.findall(r"https://[a-z0-9-]+\.trycloudflare\.com", text)
    return matches[-1] if matches else None


def normalize_base_url(raw: str) -> str:
    raw = raw.strip().rstrip("/")
    if not raw:
        return DEFAULT_BASE_URL
    parsed = urllib.parse.urlparse(raw)
    if parsed.path in {"", "/"}:
        return raw + "/v1"
    if parsed.path == "/chat":
        return urllib.parse.urlunparse(parsed._replace(path="/v1", query="", fragment=""))
    if parsed.path.endswith("/v1"):
        return raw
    return raw + "/v1"


def health_url_from_base(base_url: str) -> str:
    parsed = urllib.parse.urlparse(base_url)
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, "/health", "", "", ""))


def resolve_with_doh(hostname: str) -> str | None:
    queries = [
        f"https://dns.google/resolve?name={urllib.parse.quote(hostname)}&type=A",
        f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(hostname)}&type=A",
    ]
    for url in queries:
        try:
            request = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(request, timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            for answer in payload.get("Answer", []):
                value = str(answer.get("data", ""))
                if answer.get("type") == 1 and re.match(r"^\d+\.\d+\.\d+\.\d+$", value):
                    return value
        except Exception:
            continue
    return None


class ResolvedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, resolved_ip: str, timeout: float) -> None:
        super().__init__(host, timeout=timeout, context=ssl.create_default_context())
        self.resolved_ip = resolved_ip

    def connect(self) -> None:
        sock = socket.create_connection((self.resolved_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def request_bytes(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None = None,
    timeout: float = 300,
) -> tuple[int, dict[str, str], bytes]:
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""

    try:
        socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), error.read()
    except urllib.error.URLError as error:
        if not isinstance(error.reason, socket.gaierror) or parsed.scheme != "https":
            raise

    resolved_ip = resolve_with_doh(hostname)
    if not resolved_ip:
        raise urllib.error.URLError(socket.gaierror(f"No se pudo resolver {hostname} ni con DNS externo"))

    path = urllib.parse.urlunparse(("", "", parsed.path or "/", parsed.params, parsed.query, ""))
    conn = ResolvedHTTPSConnection(hostname, resolved_ip, timeout)
    conn.request(method, path, body=body, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, dict(response.getheaders()), data


def stream_lines(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes | None = None,
    timeout: float = 300,
):
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname or ""

    try:
        socket.getaddrinfo(hostname, parsed.port or 443)
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw in response:
                yield raw
            return
    except urllib.error.URLError as error:
        if not isinstance(error.reason, socket.gaierror) or parsed.scheme != "https":
            raise

    resolved_ip = resolve_with_doh(hostname)
    if not resolved_ip:
        raise urllib.error.URLError(socket.gaierror(f"No se pudo resolver {hostname} ni con DNS externo"))

    path = urllib.parse.urlunparse(("", "", parsed.path or "/", parsed.params, parsed.query, ""))
    conn = ResolvedHTTPSConnection(hostname, resolved_ip, timeout)
    try:
        conn.request(method, path, body=body, headers=headers)
        response = conn.getresponse()
        if response.status >= 400:
            detail = response.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {response.status}: {detail}")
        while True:
            raw = response.readline()
            if not raw:
                break
            yield raw
    finally:
        conn.close()


def default_base_url() -> str:
    tunnel = find_latest_tunnel_url()
    if not tunnel:
        return DEFAULT_BASE_URL
    base = normalize_base_url(tunnel)
    try:
        with urllib.request.urlopen(health_url_from_base(base), timeout=2) as response:
            if response.status == 200:
                return base
    except Exception:
        pass
    return DEFAULT_BASE_URL


class ApiChatApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Mini Nano API Chat")
        self.root.geometry("980x760")
        self.root.configure(bg="#f4f0e8")

        self.messages: list[dict[str, str]] = []
        self.queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self.busy = False
        self.current_assistant = ""

        self.base_url = tk.StringVar(value=default_base_url())
        self.model = tk.StringVar(value=DEFAULT_MODEL)
        self.api_key = tk.StringVar(value="local")
        self.stream = tk.BooleanVar(value=False)

        self._build_ui()
        self.root.after(80, self._drain_queue)

    def _build_ui(self) -> None:
        shell = tk.Frame(self.root, bg="#fffdfa", highlightbackground="#ddd5c8", highlightthickness=1)
        shell.pack(fill="both", expand=True, padx=18, pady=18)

        top = tk.Frame(shell, bg="#fffdfa")
        top.pack(fill="x", padx=16, pady=(14, 8))

        title = tk.Label(top, text="Mini Nano API Chat", bg="#fffdfa", fg="#1f2933", font=("Segoe UI", 17, "bold"))
        title.pack(side="left")
        self.status = tk.Label(top, text="Listo", bg="#fffdfa", fg="#667085", font=("Segoe UI", 10))
        self.status.pack(side="right")

        config = tk.Frame(shell, bg="#fbfaf7", highlightbackground="#ddd5c8", highlightthickness=1)
        config.pack(fill="x", padx=16, pady=(0, 10))

        self._field(config, "Base URL", self.base_url, 0, width=46)
        self._field(config, "Model", self.model, 1, width=24)
        self._field(config, "API Key", self.api_key, 2, width=22, show="*")

        stream_check = tk.Checkbutton(
            config,
            text="stream",
            variable=self.stream,
            bg="#fbfaf7",
            fg="#1f2933",
            activebackground="#fbfaf7",
            font=("Segoe UI", 10),
        )
        stream_check.grid(row=0, column=6, rowspan=2, padx=10, sticky="w")

        auto_button = tk.Button(
            config,
            text="Auto URL",
            command=self.use_current_tunnel_url,
            bg="#e9e5dc",
            fg="#1f2933",
            activebackground="#ded8ce",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=10,
        )
        auto_button.grid(row=0, column=7, rowspan=2, padx=(0, 10), sticky="we")

        test_button = tk.Button(
            config,
            text="Probar API",
            command=self.test_connection,
            bg="#265c7d",
            fg="white",
            activebackground="#1d4c68",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=10,
        )
        test_button.grid(row=0, column=8, rowspan=2, padx=(0, 10), sticky="we")

        body = tk.Frame(shell, bg="#fffdfa")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 10))

        self.chat = tk.Text(
            body,
            wrap="word",
            relief="flat",
            bg="#fffdfa",
            fg="#1f2933",
            font=("Segoe UI", 11),
            padx=12,
            pady=12,
            state="disabled",
        )
        scrollbar = tk.Scrollbar(body, command=self.chat.yview)
        self.chat.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.chat.pack(side="left", fill="both", expand=True)

        self.chat.tag_configure("user", foreground="#245c7c", spacing1=8, spacing3=8)
        self.chat.tag_configure("assistant", foreground="#1f2933", spacing1=8, spacing3=8)
        self.chat.tag_configure("system", foreground="#7a5a10", spacing1=8, spacing3=8)
        self.chat.tag_configure("error", foreground="#9f1d1d", spacing1=8, spacing3=8)

        bottom = tk.Frame(shell, bg="#fbfaf7", highlightbackground="#ddd5c8", highlightthickness=1)
        bottom.pack(fill="x")

        self.entry = tk.Entry(bottom, font=("Segoe UI", 12), relief="flat", bg="white", fg="#1f2933")
        self.entry.pack(side="left", fill="x", expand=True, padx=(12, 10), pady=12, ipady=10)
        self.entry.bind("<Return>", lambda _event: self.send())

        self.send_button = tk.Button(
            bottom,
            text="Enviar",
            command=self.send,
            bg="#265c7d",
            fg="white",
            activebackground="#1d4c68",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=10,
        )
        self.send_button.pack(side="left", padx=(0, 10), pady=12)

        self.clear_button = tk.Button(
            bottom,
            text="Limpiar",
            command=self.clear,
            bg="#e9e5dc",
            fg="#1f2933",
            activebackground="#ded8ce",
            relief="flat",
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=10,
        )
        self.clear_button.pack(side="left", padx=(0, 12), pady=12)

        self._append("system", "Cliente listo. La Base URL se normaliza automaticamente; para Cloudflare usa siempre la URL actual acabada en /v1.")

    def use_current_tunnel_url(self) -> None:
        tunnel = find_latest_tunnel_url()
        if not tunnel:
            self._append("error", "No encuentro una URL trycloudflare en cloudflared.log. Ejecuta primero Tunnel.bat.")
            return
        self.base_url.set(normalize_base_url(tunnel))
        self._append("system", f"Base URL actualizada: {self.base_url.get()}")

    def test_connection(self) -> None:
        if self.busy:
            return
        base = normalize_base_url(self.base_url.get())
        self.base_url.set(base)
        self._append("system", f"Probando API: {base}")
        threading.Thread(target=self._test_worker, daemon=True).start()

    def _field(self, parent: tk.Frame, label: str, var: tk.StringVar, column: int, width: int, show: str | None = None) -> None:
        frame = tk.Frame(parent, bg="#fbfaf7")
        frame.grid(row=0, column=column * 2, columnspan=2, padx=8, pady=8, sticky="we")
        tk.Label(frame, text=label, bg="#fbfaf7", fg="#667085", font=("Segoe UI", 9)).pack(anchor="w")
        entry = tk.Entry(frame, textvariable=var, width=width, show=show or "", relief="flat", bg="white", fg="#1f2933")
        entry.pack(fill="x", ipady=5)
        parent.grid_columnconfigure(column * 2, weight=1)

    def _append(self, role: str, text: str) -> None:
        self.chat.configure(state="normal")
        prefix = {"user": "Tu", "assistant": "Modelo", "system": "Sistema", "error": "Error"}.get(role, role)
        self.chat.insert("end", f"{prefix}: {text}\n\n", role)
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _append_assistant_delta(self, text: str) -> None:
        self.current_assistant += text
        self.chat.configure(state="normal")
        self.chat.insert("end", text, "assistant")
        self.chat.see("end")
        self.chat.configure(state="disabled")

    def _start_assistant_stream(self) -> None:
        self.current_assistant = ""
        self.chat.configure(state="normal")
        self.chat.insert("end", "Modelo: ", "assistant")
        self.chat.configure(state="disabled")

    def _finish_assistant_stream(self) -> None:
        self.chat.configure(state="normal")
        self.chat.insert("end", "\n\n", "assistant")
        self.chat.configure(state="disabled")
        if self.current_assistant.strip():
            self.messages.append({"role": "assistant", "content": self.current_assistant})

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.send_button.configure(state="disabled" if busy else "normal")
        self.status.configure(text="Generando..." if busy else "Listo")

    def clear(self) -> None:
        if self.busy:
            return
        self.messages.clear()
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        self.chat.configure(state="disabled")
        self._append("system", "Conversacion reiniciada.")

    def send(self) -> None:
        if self.busy:
            return
        text = self.entry.get().strip()
        if not text:
            return

        self.entry.delete(0, "end")
        self.messages.append({"role": "user", "content": text})
        self._append("user", text)
        self.set_busy(True)
        threading.Thread(target=self._worker, daemon=True).start()

    def _request(self) -> urllib.request.Request:
        url, data, headers = self._request_parts()
        return urllib.request.Request(url, data=data, headers=headers, method="POST")

    def _request_parts(self) -> tuple[str, bytes, dict[str, str]]:
        base = normalize_base_url(self.base_url.get())
        self.base_url.set(base)
        url = f"{base}/chat/completions"
        payload = {
            "model": self.model.get().strip() or DEFAULT_MODEL,
            "messages": self.messages,
            "stream": bool(self.stream.get()),
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream" if self.stream.get() else "application/json"}
        key = self.api_key.get().strip()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return url, data, headers

    def _auth_headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        key = self.api_key.get().strip()
        if key:
            headers["Authorization"] = f"Bearer {key}"
        return headers

    def _test_worker(self) -> None:
        try:
            base = normalize_base_url(self.base_url.get())
            health_url = health_url_from_base(base)
            status, _headers, body = request_bytes("GET", health_url, self._auth_headers(), timeout=15)
            if status >= 400:
                raise RuntimeError(f"HTTP {status}: {body.decode('utf-8', errors='replace')}")
            health_payload = json.loads(body.decode("utf-8"))

            status, _headers, body = request_bytes("GET", f"{base}/models", self._auth_headers(), timeout=15)
            if status >= 400:
                raise RuntimeError(f"HTTP {status}: {body.decode('utf-8', errors='replace')}")
            models_payload = json.loads(body.decode("utf-8"))

            model_ids = ", ".join(item.get("id", "") for item in models_payload.get("data", []))
            browser_state = "bridge conectado" if health_payload.get("browser_alive") else "bridge no conectado"
            self.queue.put(("system", f"API OK. Modelos: {model_ids or 'sin modelos'}. Estado: {browser_state}."))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code == 530 or "Cloudflare Tunnel error" in detail:
                self.queue.put(("error", "Cloudflare 530: la URL publica esta cerrada o es antigua. Arranca Tunnel.bat y copia la URL nueva."))
            else:
                self.queue.put(("error", f"Prueba fallida HTTP {error.code}: {detail}"))
        except urllib.error.URLError as error:
            reason = error.reason
            if isinstance(reason, socket.gaierror):
                self.queue.put(("error", "DNS no resuelve esa URL. En otro ordenador, revisa que el tunel siga vivo y que la URL sea la ultima generada."))
            else:
                self.queue.put(("error", f"Prueba fallida: {error}"))
        except Exception as error:
            self.queue.put(("error", f"Prueba fallida: {error}"))

    def _worker(self) -> None:
        try:
            if self.stream.get():
                self._stream_worker()
            else:
                self._json_worker()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            if error.code == 530 or "Cloudflare Tunnel error" in detail:
                self.queue.put((
                    "error",
                    "Cloudflare responde 530: esa URL publica esta cerrada o es antigua. "
                    "Ejecuta Tunnel.bat y pulsa Auto URL, o usa http://127.0.0.1:8788/v1 en esta maquina.",
                ))
            else:
                self.queue.put(("error", f"HTTP {error.code}: {detail}"))
        except urllib.error.URLError as error:
            reason = error.reason
            if isinstance(reason, socket.gaierror):
                self.queue.put((
                    "error",
                    "DNS no resuelve esa Base URL. Si es trycloudflare.com, ejecuta "
                    "FixCurrentTunnelHosts.bat o usa http://127.0.0.1:8788/v1 en local.",
                ))
            else:
                self.queue.put(("error", str(error)))
        except Exception as error:
            self.queue.put(("error", str(error)))
        finally:
            self.queue.put(("done_busy", ""))

    def _json_worker(self) -> None:
        url, data, headers = self._request_parts()
        status, _response_headers, body = request_bytes("POST", url, headers, body=data, timeout=300)
        if status >= 400:
            raise RuntimeError(f"HTTP {status}: {body.decode('utf-8', errors='replace')}")
        payload = json.loads(body.decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        self.messages.append({"role": "assistant", "content": content})
        self.queue.put(("assistant", content))

    def _stream_worker(self) -> None:
        self.queue.put(("stream_start", ""))
        url, data, headers = self._request_parts()
        for raw in stream_lines("POST", url, headers, body=data, timeout=300):
            line = raw.decode("utf-8", errors="replace").strip()
            if not line or not line.startswith("data: "):
                continue
            data_text = line[6:]
            if data_text == "[DONE]":
                break
            payload = json.loads(data_text)
            if "error" in payload:
                raise RuntimeError(payload["error"].get("message", "API error"))
            delta = payload["choices"][0].get("delta", {})
            content = delta.get("content")
            if content:
                self.queue.put(("delta", content))
        self.queue.put(("stream_done", ""))

    def _drain_queue(self) -> None:
        while True:
            try:
                event, value = self.queue.get_nowait()
            except queue.Empty:
                break

            if event == "assistant":
                self._append("assistant", value)
            elif event == "system":
                self._append("system", value)
            elif event == "stream_start":
                self._start_assistant_stream()
            elif event == "delta":
                self._append_assistant_delta(value)
            elif event == "stream_done":
                self._finish_assistant_stream()
            elif event == "error":
                self._append("error", value)
            elif event == "done_busy":
                self.set_busy(False)

        self.root.after(80, self._drain_queue)


def main() -> None:
    root = tk.Tk()
    ApiChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
