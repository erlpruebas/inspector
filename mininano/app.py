from __future__ import annotations

import argparse
import json
import queue
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4
import webbrowser
import urllib.request


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8787
MOCK_MODE = False


def json_bytes(payload: dict) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


@dataclass
class RequestRecord:
    request_id: str
    messages: list[dict]
    created_at: float = field(default_factory=time.time)
    events: "queue.Queue[dict]" = field(default_factory=queue.Queue)
    done: bool = False


class BridgeState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: "queue.Queue[dict]" = queue.Queue()
        self._records: dict[str, RequestRecord] = {}
        self._browser_seen_at = 0.0
        self.last_error: str | None = None

    def submit_request(self, messages: list[dict]) -> RequestRecord:
        record = RequestRecord(request_id=uuid4().hex[:12], messages=messages)
        with self._lock:
            self._records[record.request_id] = record
        self._pending.put({"id": record.request_id, "messages": messages})
        return record

    def next_request(self) -> dict | None:
        try:
            payload = self._pending.get_nowait()
        except queue.Empty:
            return None

        self._browser_seen_at = time.time()
        return payload

    def browser_alive(self) -> bool:
        return (time.time() - self._browser_seen_at) < 3.0

    def push_event(self, request_id: str, event: dict) -> None:
        with self._lock:
            record = self._records.get(request_id)
        if not record:
            return
        record.events.put(event)
        if event.get("type") in {"done", "error"}:
            record.done = True

    def get_record(self, request_id: str) -> RequestRecord | None:
        with self._lock:
            return self._records.get(request_id)


STATE = BridgeState()


class MiniNanoHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, payload: dict, status: int = 200) -> None:
        data = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/status":
            self._send_json(
                {
                    "browser_alive": STATE.browser_alive(),
                    "queue_size": STATE._pending.qsize(),
                    "last_error": STATE.last_error,
                }
            )
            return

        if parsed.path == "/api/browser/next":
            request = STATE.next_request()
            self._send_json({"request": request})
            return

        if parsed.path == "/api/gui/events":
            params = parse_qs(parsed.query)
            request_id = params.get("id", [""])[0]
            record = STATE.get_record(request_id)
            if not record:
                self._send_json({"events": []})
                return

            events = []
            while True:
                try:
                    events.append(record.events.get_nowait())
                except queue.Empty:
                    break
            self._send_json({"events": events, "done": record.done})
            return

        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            payload = {}

        if parsed.path == "/api/gui/submit":
            messages = payload.get("messages") or []
            record = STATE.submit_request(messages)
            self._send_json({"id": record.request_id})
            return

        if parsed.path == "/api/browser/event":
            request_id = payload.get("request_id", "")
            event = {k: v for k, v in payload.items() if k != "request_id"}
            STATE.push_event(request_id, event)
            if event.get("type") == "error":
                STATE.last_error = event.get("error")
            self._send_json({"ok": True})
            return

        self.send_error(HTTPStatus.NOT_FOUND)


class ScrollableChat:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Mini Nano Chat")
        self.root.geometry("980x760")
        self.root.configure(bg="#f4f0e8")

        self.history: list[dict] = []
        self.active_request: RequestRecord | None = None
        self.bubble_by_request: dict[str, tk.Label] = {}
        self.current_text_by_request: dict[str, str] = {}

        self._build_ui()
        self.root.after(120, self._poll_browser_status)
        self.root.after(120, self._poll_events)

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg="#f4f0e8")
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        shell = tk.Frame(outer, bg="#fffdfa", highlightbackground="#ddd5c8", highlightthickness=1)
        shell.pack(fill="both", expand=True)

        top = tk.Frame(shell, bg="#fffdfa")
        top.pack(fill="x", padx=18, pady=(16, 12))
        title = tk.Label(top, text="Mini Nano Chat", font=("Segoe UI", 17, "bold"), bg="#fffdfa", fg="#1f2933")
        title.pack(side="left")
        self.status = tk.Label(top, text="Conectando...", font=("Segoe UI", 10), bg="#fffdfa", fg="#6b7280")
        self.status.pack(side="right")

        self.canvas = tk.Canvas(shell, bg="#fffdfa", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(shell, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.chat_frame = tk.Frame(self.canvas, bg="#fffdfa")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.chat_frame.bind("<Configure>", self._sync_scrollregion)
        self.canvas.bind("<Configure>", self._resize_canvas_window)

        bottom = tk.Frame(shell, bg="#fbfaf7", highlightbackground="#ddd5c8", highlightthickness=1)
        bottom.pack(fill="x")

        self.entry = tk.Entry(bottom, font=("Segoe UI", 12), relief="flat", bg="white", fg="#1f2933")
        self.entry.pack(side="left", fill="x", expand=True, padx=(12, 10), pady=12, ipady=10)
        self.entry.bind("<Return>", lambda _: self.send_message())

        self.send_btn = tk.Button(
            bottom,
            text="Enviar",
            command=self.send_message,
            bg="#265c7d",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            activebackground="#1d4c68",
            activeforeground="white",
            padx=16,
            pady=10,
        )
        self.send_btn.pack(side="left", padx=(0, 10), pady=12)

        self.sample_btn = tk.Button(
            bottom,
            text="Prueba",
            command=self.load_sample,
            bg="#e9e5dc",
            fg="#1f2933",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            activebackground="#ded8ce",
            activeforeground="#1f2933",
            padx=16,
            pady=10,
        )
        self.sample_btn.pack(side="left", padx=(0, 12), pady=12)

        self.add_message("system", "La app está lista. Abre la pestaña del navegador para que actúe como puente.")

    def _sync_scrollregion(self, _event=None) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _resize_canvas_window(self, event) -> None:
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _scroll_to_bottom(self) -> None:
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def add_message(self, role: str, text: str) -> tk.Label:
        row = tk.Frame(self.chat_frame, bg="#fffdfa")
        row.pack(fill="x", padx=16, pady=6)

        if role == "user":
            bubble_bg, fg, anchor = "#265c7d", "white", "e"
        elif role == "assistant":
            bubble_bg, fg, anchor = "#eaf4ec", "#1f2933", "w"
        elif role == "error":
            bubble_bg, fg, anchor = "#fde8e8", "#7f1d1d", "w"
        else:
            bubble_bg, fg, anchor = "#fdf3d2", "#51452b", "center"

        wrapper = tk.Frame(row, bg="#fffdfa")
        wrapper.pack(side="right" if role == "user" else "left", anchor=anchor, fill="x", expand=True)

        label = tk.Label(
            wrapper,
            text=text,
            wraplength=640,
            justify="left",
            bg=bubble_bg,
            fg=fg,
            font=("Segoe UI", 11),
            padx=14,
            pady=10,
            highlightthickness=1,
            highlightbackground="#d8d1c4" if role != "user" else bubble_bg,
            relief="flat",
        )
        label.pack(side="right" if role == "user" else "left", anchor=anchor)
        self._scroll_to_bottom()
        return label

    def set_status(self, text: str) -> None:
        self.status.configure(text=text)

    def send_message(self) -> None:
        text = self.entry.get().strip()
        if not text:
            return

        if self.active_request and not self.active_request.done:
            self.add_message("system", "Espera a que termine la respuesta actual.")
            return

        self.entry.delete(0, "end")
        self.history.append({"role": "user", "content": text})
        self.add_message("user", text)

        assistant_label = self.add_message("assistant", "")
        record = STATE.submit_request(list(self.history))
        self.active_request = record
        self.bubble_by_request[record.request_id] = assistant_label
        self.current_text_by_request[record.request_id] = ""
        self.set_status(f"Enviando {record.request_id}...")

    def load_sample(self) -> None:
        self.entry.delete(0, "end")
        self.entry.insert(0, "hola como preparo un cafe con una maquina de filtro")
        self.send_message()

    def _poll_browser_status(self) -> None:
        alive = STATE.browser_alive()
        if alive:
            self.set_status("Puente conectado")
        elif self.active_request and not self.active_request.done:
            self.set_status("Esperando al navegador...")
        else:
            self.set_status("Esperando al navegador...")
        self.root.after(250, self._poll_browser_status)

    def _poll_events(self) -> None:
        if self.active_request:
            record = STATE.get_record(self.active_request.request_id)
            if record:
                while True:
                    try:
                        event = record.events.get_nowait()
                    except queue.Empty:
                        break

                    request_id = record.request_id
                    bubble = self.bubble_by_request.get(request_id)
                    if not bubble:
                        continue

                    if event["type"] == "started":
                        bubble.configure(text="")
                    elif event["type"] == "delta":
                        current = self.current_text_by_request.get(request_id, "")
                        current = event.get("content") or (current + event.get("delta", ""))
                        self.current_text_by_request[request_id] = current
                        bubble.configure(text=current)
                        self._scroll_to_bottom()
                    elif event["type"] == "done":
                        bubble.configure(text=event.get("content", self.current_text_by_request.get(request_id, "")))
                        self.history.append({"role": "assistant", "content": bubble.cget("text")})
                        self.current_text_by_request[request_id] = bubble.cget("text")
                        self.active_request = None
                        self.set_status("Listo")
                    elif event["type"] == "error":
                        bubble.configure(text=f"Error: {event.get('error', 'desconocido')}", bg="#fde8e8", fg="#7f1d1d")
                        self.active_request = None
                        self.set_status("Error")

        self.root.after(80, self._poll_events)


def serve_http() -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((HOST, PORT), MiniNanoHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def open_browser() -> None:
    url = f"http://{HOST}:{PORT}/index.html"
    if MOCK_MODE:
        url += "?mock=1"
    webbrowser.open(url)


def smoke_test_server() -> None:
    with urllib.request.urlopen(f"http://{HOST}:{PORT}/index.html", timeout=5) as response:
        assert response.status == 200
    with urllib.request.urlopen(f"http://{HOST}:{PORT}/api/status", timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
        assert "browser_alive" in payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Mini Nano bridge app")
    parser.add_argument("--mock", action="store_true", help="open the browser bridge in mock mode")
    return parser.parse_args()


def main() -> None:
    global MOCK_MODE
    args = parse_args()
    MOCK_MODE = args.mock
    server = serve_http()
    open_browser()
    smoke_test_server()

    root = tk.Tk()
    app = ScrollableChat(root)

    def on_close() -> None:
        server.shutdown()
        server.server_close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
