from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ai.opencode import OpenCodeBackend
from ai.python_shim import OpenAICompatBackend


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # keep test output clean
        pass

    def _send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/v1/models":
            self._send_json({"data": [{"id": "mock-model"}]})
        elif self.path == "/global/health":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        if self.path == "/v1/chat/completions":
            self._stream_sse()
        elif self.path == "/session":
            self._send_json({"id": "sess-1"})
        elif self.path.startswith("/session/") and self.path.endswith("/message"):
            self._send_json({"parts": [{"type": "text", "text": "Hello from opencode"}]})
        else:
            self.send_response(404)
            self.end_headers()

    def _stream_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for token in ("Hello", " world"):
            chunk = json.dumps({"choices": [{"delta": {"content": token}}]})
            self.wfile.write(f"data: {chunk}\n\n".encode("utf-8"))
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


@pytest.fixture
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    try:
        yield port
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_openai_compat_against_real_server(server):
    backend = OpenAICompatBackend(base_url=f"http://127.0.0.1:{server}", model="mock")
    assert backend.is_available()
    deltas: list[str] = []
    reply = backend.complete("sys", [{"role": "user", "content": "hi"}], deltas.append)
    assert reply == "Hello world"
    assert deltas == ["Hello", " world"]


def test_opencode_against_real_server(server, monkeypatch):
    backend = OpenCodeBackend(model="mock/mock")
    # Point the adapter at our local server instead of spawning the real binary.
    monkeypatch.setattr(OpenCodeBackend, "start", lambda self: None)
    backend.base_url = f"http://127.0.0.1:{server}"
    backend.port = server

    assert backend.is_available()
    deltas: list[str] = []
    reply = backend.complete(
        "be helpful", [{"role": "user", "content": "hi"}], deltas.append
    )
    assert "opencode" in reply
    assert deltas and deltas[0] == reply


def test_opencode_against_external_url(server, monkeypatch):
    # Exercises the real OPENCODE_BASE_URL code path (start() becomes a no-op,
    # no binary spawned) against a live local server.
    monkeypatch.setenv("OPENCODE_BASE_URL", f"http://127.0.0.1:{server}")
    backend = OpenCodeBackend(model="mock/mock")

    assert backend._external is True
    assert backend.start() is True
    assert backend.is_available()
    reply = backend.complete("be helpful", [{"role": "user", "content": "hi"}])
    assert "opencode" in reply
