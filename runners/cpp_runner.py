from __future__ import annotations

import os
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable

if os.name == "nt":
    _CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class CppRunner:
    """Runs C++ projects: compiles with g++/clang++, then executes the binary."""

    def __init__(self, interpreter: str | None = None) -> None:
        self.interpreter = interpreter
        self._process: subprocess.Popen | None = None

    def _compiler(self) -> str:
        for name in ("g++", "clang++", "cl"):
            path = shutil.which(name)
            if path:
                return path
        return "g++"

    def _compile(self, cwd: Path, script: str, on_line: Callable[[str], None]) -> str | None:
        binary = Path(script).stem
        if os.name == "nt":
            binary = binary + ".exe"
        result = subprocess.run(
            [self._compiler(), script, "-o", binary],
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
        return binary

    def start_and_stream(
        self,
        cwd: Path,
        script: str = "game.cpp",
        on_line: Callable[[str], None] | None = None,
    ) -> int:
        def emit(line: str) -> None:
            if on_line is not None:
                on_line(line)

        binary = self._compile(cwd, Path(script).name, emit)
        if binary is None:
            return 1
        binary_path = Path(cwd) / binary
        run_cmd = [str(binary_path)]
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
        self._process = subprocess.Popen(run_cmd, **kwargs)

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
