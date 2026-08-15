from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable


def _is_real_python(path: str) -> bool:
    """Validate that a Python executable is real (not Windows Store stub)."""
    try:
        result = subprocess.run(
            [path, "-c", "print(1)"],
            capture_output=True,
            timeout=5,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return result.returncode == 0 and "1" in result.stdout
    except Exception:
        return False


def find_python() -> str:
    """Locate a real Python interpreter to run user projects with.

    When not frozen we are already running inside a working Python, so just use
    ``sys.executable``. This also avoids the Windows Store ``python.exe``
    app-execution alias, which ``shutil.which`` can resolve to a stub that prints
    "Python was not found" and exits 9009 instead of running code.

    In a PyInstaller bundle ``sys.executable`` is the frozen ``.exe``; running it
    again would re-launch the whole app, so we resolve ``python``/``python3`` from
    the environment instead.
    """
    if not getattr(sys, "frozen", False):
        return sys.executable
    for name in ("python", "python3"):
        found = shutil.which(name)
        if found and _is_real_python(found):
            return found
    # Fallback - try common install locations
    for candidate in (
        r"C:\Python314\python.exe",
        r"C:\Python313\python.exe",
        r"C:\Python312\python.exe",
        r"C:\Program Files\Python314\python.exe",
        r"C:\Program Files\Python313\python.exe",
        r"C:\Program Files\Python312\python.exe",
    ):
        if _is_real_python(candidate):
            return candidate
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