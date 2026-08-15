from __future__ import annotations

import os
import subprocess
import threading
from pathlib import Path
from typing import Callable

if os.name == "nt":
    _CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class JavaRunner:
    """Runs Java projects: compiles then executes the main class."""

    def __init__(self, interpreter: str | None = None) -> None:
        self.interpreter = interpreter
        self._process: subprocess.Popen | None = None

    def _compile(self, cwd: Path, script: str, on_line: Callable[[str], None]) -> bool:
        result = subprocess.run(
            ["javac", script],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if result.returncode != 0:
            for line in (result.stderr or "").splitlines():
                on_line(line)
            return False
        return True

    def start_and_stream(
        self,
        cwd: Path,
        script: str = "Game.java",
        on_line: Callable[[str], None] | None = None,
    ) -> int:
        def emit(line: str) -> None:
            if on_line is not None:
                on_line(line)

        if not self._compile(cwd, Path(script).name, emit):
            return 1
        main_class = Path(script).stem
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
        self._process = subprocess.Popen(["java", main_class], **kwargs)

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
