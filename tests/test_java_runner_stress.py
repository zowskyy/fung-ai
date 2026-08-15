"""Stress tests for JavaRunner — exercise compile, run, panic, stop."""
from __future__ import annotations

import os
import shutil
import textwrap
import time
from pathlib import Path

import pytest

from runners.java_runner import JavaRunner


JAVAC = shutil.which("javac")
pytestmark = pytest.mark.skipif(
    JAVAC is None, reason="javac not installed"
)


def _write_java(tmp_path, filename, code):
    path = os.path.join(str(tmp_path), filename)
    with open(path, "w") as f:
        f.write(textwrap.dedent(code))
    return path


def test_normal_program(tmp_path):
    """A well-formed Java program should compile and exit cleanly."""
    main = _write_java(
        tmp_path, "Hello.java", """\
        public class Hello {
            public static void main(String[] args) {
                System.out.println("JavaRunner OK");
            }
        }
        """
    )
    runner = JavaRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path,
        script="Hello.java",
        on_line=output_lines.append,
    )
    assert code == 0
    assert "JavaRunner OK" in "\n".join(output_lines)


def test_compile_error_captured(tmp_path):
    """A syntax error should produce non-zero exit with compiler messages."""
    _write_java(
        tmp_path, "Bad.java", """\
        public class Bad {
            this is not valid java !!!
        }
        """
    )
    runner = JavaRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path,
        script="Bad.java",
        on_line=output_lines.append,
    )
    assert code != 0
    joined = "\n".join(output_lines)
    assert "error" in joined.lower()


def test_runtime_exception_captured(tmp_path):
    """A runtime exception should produce non-zero exit and visible stack trace."""
    _write_java(
        tmp_path, "Boom.java", """\
        public class Boom {
            public static void main(String[] args) {
                int x = 1 / 0;
            }
        }
        """
    )
    runner = JavaRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path,
        script="Boom.java",
        on_line=output_lines.append,
    )
    assert code != 0
    joined = "\n".join(output_lines)
    assert "exception" in joined.lower() or "error" in joined.lower()


def test_stop_terminates_process(tmp_path):
    """stop() should terminate a long-running Java process."""
    _write_java(
        tmp_path, "Spin.java", """\
        public class Spin {
            public static void main(String[] args) {
                while (true) {
                    System.out.println("spinning");
                }
            }
        }
        """
    )
    runner = JavaRunner()

    import threading
    from pathlib import Path

    output_lines: list[str] = []
    result_code: list[int] = []

    def run():
        result_code.append(
            runner.start_and_stream(
                cwd=tmp_path,
                script="Spin.java",
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
