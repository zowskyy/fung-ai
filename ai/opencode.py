from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Callable

from .backend import AIBackend


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class OpenCodeBackend(AIBackend):
    """Drives a real opencode server the same way opencode's own clients do.

    If ``OPENCODE_BASE_URL`` is set (or passed to the constructor), the backend
    connects to that already-running server instead of spawning the opencode
    binary itself. This is how Creator reaches the user's own opencode instance,
    or a locally-emulated one, without requiring the CLI to be installed.
    """

    name = "opencode"

    def __init__(self, model: str = "anthropic/claude-sonnet-4-5", base_url: str | None = None):
        self.model = model
        external = base_url or os.environ.get("OPENCODE_BASE_URL")
        if external:
            self.base_url = external.rstrip("/")
            self.port = int(self.base_url.rsplit(":", 1)[-1]) if ":" in self.base_url else 0
            self.proc: subprocess.Popen | None = None
            self._external = True
        else:
            self.port = _free_port()
            self.base_url = f"http://127.0.0.1:{self.port}"
            self.proc = None
            self._external = False

    @staticmethod
    def find_executable() -> str | None:
        return shutil.which("opencode")

    def start(self) -> bool:
        if self._external:
            return self.is_available()
        if self.proc is not None and self.proc.poll() is None:
            return self.is_available()
        exe = self.find_executable()
        if not exe:
            return False
        base_dir = Path.home() / ".creator" / "opencode"
        base_dir.mkdir(parents=True, exist_ok=True)
        self.proc = subprocess.Popen(
            [exe, "serve", "--port", str(self.port), "--hostname", "127.0.0.1"],
            cwd=str(base_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        deadline = time.time() + 20
        while time.time() < deadline:
            if self.is_available():
                return True
            if self.proc.poll() is not None:
                return False
            time.sleep(0.4)
        return False

    def is_available(self) -> bool:
        try:
            with urllib.request.urlopen(self.base_url + "/global/health", timeout=3) as resp:
                return resp.status == 200
        except Exception:
            return False

    def _session_id(self) -> str:
        body = json.dumps({"title": "Creator helper"}).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + "/session",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["id"]

    def complete(
        self,
        system: str,
        messages: list[dict],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        if not self.is_available():
            raise RuntimeError("opencode server is not running.")
        session_id = self._session_id()
        user_text = "".join(m.get("content", "") for m in messages)
        provider, _, model = self.model.partition("/")
        payload = {
            "parts": [{"type": "text", "text": f"{system}\n\nUser: {user_text}"}],
            "model": {"providerID": provider, "modelID": model},
        }
        request = urllib.request.Request(
            self.base_url + f"/session/{session_id}/message",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=300) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        reply = "".join(
            part.get("text", "")
            for part in result.get("parts", [])
            if part.get("type") == "text"
        ).strip()
        if not reply:
            raise RuntimeError("opencode returned an empty reply.")
        if on_delta is not None:
            on_delta(reply)
        return reply
