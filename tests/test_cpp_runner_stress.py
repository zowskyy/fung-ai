"""Stress tests for CppRunner — exercise compile, run, crash, stop."""
from __future__ import annotations

import os
import shutil
import textwrap
import time

from pathlib import Path

import pytest

from runners.cpp_runner import CppRunner


GXX = shutil.which("g++")
pytestmark = pytest.mark.skipif(
    GXX is None, reason="g++ not installed"
)


def _write_cpp(tmp_path, filename, code):
    path = Path(tmp_path) / filename
    path.write_text(textwrap.dedent(code))
    return path


def test_normal_program(tmp_path):
    """A well-formed C++ program should compile and exit cleanly."""
    _write_cpp(
        tmp_path, "Hello.cpp", """\
        #include <iostream>
        int main() { std::cout << "CppRunner OK" << std::endl; return 0; }
        """
    )
    runner = CppRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path, script="Hello.cpp", on_line=output_lines.append
    )
    assert code == 0
    assert "CppRunner OK" in "\n".join(output_lines)


def test_compile_error_captured(tmp_path):
    """A syntax error should produce non-zero exit with compiler messages."""
    _write_cpp(
        tmp_path, "Bad.cpp", """\
        #include <iostream>
        this is not valid c++ !!!
        """
    )
    runner = CppRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path, script="Bad.cpp", on_line=output_lines.append
    )
    assert code != 0
    joined = "\n".join(output_lines)
    assert "error" in joined.lower()


def test_runtime_crash_captured(tmp_path):
    """A segmentation fault should produce non-zero exit."""
    _write_cpp(
        tmp_path, "Crash.cpp", """\
        int main() {
            int* p = nullptr;
            return *p;
        }
        """
    )
    runner = CppRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path, script="Crash.cpp", on_line=output_lines.append
    )
    assert code != 0
    joined = "\n".join(output_lines)
    # On some platforms, segfaults may not produce visible stderr
    # Just verify non-zero exit code


def test_infinite_loop_terminated(tmp_path):
    """An infinite loop should be killable via stop() from another thread."""
    _write_cpp(
        tmp_path, "Spin.cpp", """\
        #include <iostream>
        int main() {
            while (true) { std::cout << "spinning" << std::endl; }
            return 0;
        }
        """
    )
    runner = CppRunner()

    import threading

    output_lines: list[str] = []
    result_code: list[int] = []

    def run():
        result_code.append(
            runner.start_and_stream(
                cwd=tmp_path, script="Spin.cpp", on_line=output_lines.append
            )
        )

    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(5)  # let it compile and start spinning
    runner.stop()
    thread.join(timeout=15)
    assert not thread.is_alive(), "Process did not terminate after stop()"
    assert result_code, "Process was not running when stop() was called"
