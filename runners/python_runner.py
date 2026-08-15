from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


def find_python() -> str:
    """Locate a real Python interpreter on PATH.

    In a PyInstaller bundle ``sys.executable`` is the frozen ``.exe``; running it
    again would re-launch the whole app, so we must resolve ``python``/``python3``
    from the environment instead.
    """
    for name in ("python", "python3"):
        found = shutil.which(name)
        if found:
            return found
    if not getattr(sys, "frozen", False):
        return sys.executable
    return "python"


class PythonRunner:
    def __init__(self, interpreter: str | None = None):
        self.interpreter = interpreter or find_python()
        self._process: subprocess.Popen | None = None

    def start_and_stream(
        self,
        cwd: Path,
        script: str = "game.py",
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
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self._process = subprocess.Popen([self.interpreter, script], **kwargs)
        if on_line and self._process.stdout:
            for raw in self._process.stdout:
                on_line(raw.rstrip("\r\n"))
        return self._process.wait()

    def stop(self) -> None:
        proc = self._process
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
