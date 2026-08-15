from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from ai.python_shim import OpenAICompatBackend


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/v1/models":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"data": []}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length))
        assert payload["stream"] is True
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        for token in ["Hel", "lo", "!"]:
            event = json.dumps({"choices": [{"delta": {"content": token}}]})
            self.wfile.write(f"data: {event}\n\n".encode("utf-8"))
        self.wfile.write(b"data: [DONE]\n\n")


@pytest.fixture
def server():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_shim_available(server):
    backend = OpenAICompatBackend(server)
    assert backend.is_available()


def test_shim_streams(server):
    backend = OpenAICompatBackend(server)
    received: list[str] = []
    reply = backend.complete(
        "sys", [{"role": "user", "content": "hi"}], received.append
    )
    assert reply == "Hello!"
    assert "".join(received) == "Hello!"
