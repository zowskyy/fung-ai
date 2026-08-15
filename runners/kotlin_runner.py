from __future__ import annotations

import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable

if os.name == "nt":
    _CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def find_kotlin() -> str:
    """Locate the kotlinc compiler.

    On Windows the compiler ships as ``kotlinc.bat``; ``CreateProcess`` will not
    resolve the extension-less name, so resolve it explicitly via ``shutil.which``
    (which honours ``PATHEXT``).
    """
    for name in ("kotlinc", "kotlinc.bat", "kotlinc.cmd"):
        found = shutil.which(name)
        if found:
            return found
    return "kotlinc"


class KotlinRunner:
    """Runs Kotlin projects: compiles to a JAR with kotlinc, then executes via java."""

    def __init__(self, interpreter: str | None = None) -> None:
        self.interpreter = interpreter or find_kotlin()
        self._process: subprocess.Popen | None = None

    def _compile(self, cwd: Path, script: str, on_line: Callable[[str], None]) -> str | None:
        jar_name = Path(script).stem + ".jar"
        result = subprocess.run(
            [self.interpreter, script, "-include-runtime", "-d", jar_name],
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
            return None
        return jar_name

    def start_and_stream(
        self,
        cwd: Path,
        script: str = "Game.kt",
        on_line: Callable[[str], None] | None = None,
    ) -> int:
        def emit(line: str) -> None:
            if on_line is not None:
                on_line(line)

        jar = self._compile(cwd, Path(script).name, emit)
        if jar is None:
            return 1
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
        self._process = subprocess.Popen(["java", "-jar", jar], **kwargs)

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
