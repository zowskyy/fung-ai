"""A tiny, dependency-free opencode-protocol server for local testing.

It speaks the exact subset of opencode's HTTP API that Creator's
``OpenCodeBackend`` uses, so you can test the adapter without installing the
real opencode CLI or any model:

    GET  /global/health              -> 200 (is the server up?)
    POST /session                    -> {"id": "..."}  (start a session)
    POST /session/<id>/message       -> {"parts": [{"type": "text", "text": "..."}]}

Run it:

    python tools/opencode_mock_server.py --port 8765

Then point Creator at it with the OPENCODE_BASE_URL env var (or set
``opencode_base_url`` in ~/.creator/auth.json):

    set OPENCODE_BASE_URL=http://127.0.0.1:8765
    python run.py
"""

from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:
        pass

    def _json(self, obj: dict, status: int = 200) -> None:
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/global/health":
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        if self.path == "/session":
            self._json({"id": "mock-session-1"})
        elif self.path.startswith("/session/") and self.path.endswith("/message"):
            self._json(
                {
                    "parts": [
                        {
                            "type": "text",
                            "text": (
                                "Hello from the mock opencode server. Connect Creator to a "
                                "real OpenAI-compatible endpoint (Ollama, OpenRouter, Together, "
                                "Groq, ...) with your own key to get live model responses."
                            ),
                        }
                    ]
                }
            )
        else:
            self.send_response(404)
            self.end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mock opencode server for testing Creator.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    url = f"http://{args.host}:{args.port}"
    print(f"Mock opencode server listening on {url}")
    print(f"Point Creator at it with:  set OPENCODE_BASE_URL={url}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
