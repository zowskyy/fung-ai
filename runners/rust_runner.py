from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from typing import Callable

if os.name == "nt":
    _CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class RustRunner:
    """Runs Rust projects via ``cargo run`` (handles compile + execute)."""

    def __init__(self, interpreter: str | None = None) -> None:
        self.interpreter = interpreter
        self._process: subprocess.Popen | None = None

    def start_and_stream(
        self,
        cwd: Path,
        script: str = ".",
        on_line: Callable[[str], None] | None = None,
    ) -> int:
        kwargs: dict = dict(
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        if os.name == "nt":
            kwargs["creationflags"] = _CREATE_NO_WINDOW
        self._process = subprocess.Popen(["cargo", "run"], **kwargs)

        if on_line and self._process.stdout:
            def _reader():
                for raw in self._process.stdout:
                    try:
                        on_line(raw.rstrip("\r\n"))
                    except Exception:
                        break
            threading.Thread(target=_reader, daemon=True).start()

        return self._process.wait()

    def stop(self) -> None:
        proc = self._process
        if proc is not None and proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
