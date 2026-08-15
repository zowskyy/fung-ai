"""Stress tests for KotlinRunner — exercise compile, run, error, stop."""
from __future__ import annotations

import os
import shutil
import textwrap
import time
from pathlib import Path

import pytest

from runners.kotlin_runner import KotlinRunner


KOTLINC = shutil.which("kotlinc")
pytestmark = pytest.mark.skipif(
    KOTLINC is None, reason="kotlinc not installed"
)


def _write_kt(tmp_path, filename, code):
    path = os.path.join(str(tmp_path), filename)
    with open(path, "w") as f:
        f.write(textwrap.dedent(code))
    return path


def test_normal_program(tmp_path):
    """A well-formed Kotlin program should compile and exit cleanly."""
    _write_kt(
        tmp_path, "Hello.kt", """\
        fun main() {
            println("KotlinRunner OK")
        }
        """
    )
    runner = KotlinRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path,
        script="Hello.kt",
        on_line=output_lines.append,
    )
    assert code == 0
    assert "KotlinRunner OK" in "\n".join(output_lines)


def test_compile_error_captured(tmp_path):
    """A syntax error should produce non-zero exit with compiler messages."""
    _write_kt(
        tmp_path, "Bad.kt", """\
        fun main() {
            this is not valid kotlin !!!
        }
        """
    )
    runner = KotlinRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path,
        script="Bad.kt",
        on_line=output_lines.append,
    )
    assert code != 0
    joined = "\n".join(output_lines)
    assert "error" in joined.lower()


def test_runtime_exception_captured(tmp_path):
    """A runtime exception should produce non-zero exit and visible stack trace."""
    _write_kt(
        tmp_path, "Boom.kt", """\
        fun main() {
            val x = 1 / 0
        }
        """
    )
    runner = KotlinRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path,
        script="Boom.kt",
        on_line=output_lines.append,
    )
    assert code != 0
    joined = "\n".join(output_lines)
    assert "exception" in joined.lower() or "error" in joined.lower()


def test_stop_terminates_process(tmp_path):
    """stop() should terminate a long-running Kotlin process."""
    _write_kt(
        tmp_path, "Spin.kt", """\
        fun main() {
            while (true) {
                println("spinning")
            }
        }
        """
    )
    runner = KotlinRunner()

    import threading

    output_lines: list[str] = []
    result_code: list[int] = []

    def run():
        result_code.append(
            runner.start_and_stream(
                cwd=tmp_path,
                script="Spin.kt",
                on_line=output_lines.append,
            )
        )

    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(3)  # let it compile and start spinning
    runner.stop()
    thread.join(timeout=15)
    assert not thread.is_alive(), "Process did not terminate after stop()"
    assert result_code, "Process was not running when stop() was called"
