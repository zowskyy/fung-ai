"""Stress tests for JavaScriptRunner — exercise run, crash, stop."""
from __future__ import annotations

import os
import shutil
import textwrap
import time

from pathlib import Path

import pytest

from runners.javascript_runner import JavaScriptRunner


NODE = shutil.which("node")
pytestmark = pytest.mark.skipif(
    NODE is None, reason="node not installed"
)


def _write_js(tmp_path, filename, code):
    path = Path(tmp_path) / filename
    path.write_text(textwrap.dedent(code))
    return path


def test_normal_program(tmp_path):
    """A well-formed JavaScript program should run and exit cleanly."""
    _write_js(
        tmp_path, "Hello.js", """\
        console.log("JavaScriptRunner OK");
        """
    )
    runner = JavaScriptRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path, script="Hello.js", on_line=output_lines.append
    )
    assert code == 0
    assert "JavaScriptRunner OK" in "\n".join(output_lines)


def test_runtime_error_captured(tmp_path):
    """A JavaScript exception should produce non-zero exit with error output."""
    _write_js(
        tmp_path, "Boom.js", """\
        throw new Error("intentional crash");
        """
    )
    runner = JavaScriptRunner()
    output_lines: list[str] = []
    code = runner.start_and_stream(
        cwd=tmp_path, script="Boom.js", on_line=output_lines.append
    )
    assert code != 0
    joined = "\n".join(output_lines)
    assert "error" in joined.lower() or "boom" in joined.lower()


def test_infinite_loop_terminated(tmp_path):
    """An infinite loop should be killable via stop() from another thread."""
    _write_js(
        tmp_path, "Spin.js", """\
        setInterval(() => { console.log("spinning"); }, 10);
        """
    )
    runner = JavaScriptRunner()

    import threading

    output_lines: list[str] = []
    result_code: list[int] = []

    def run():
        result_code.append(
            runner.start_and_stream(
                cwd=tmp_path, script="Spin.js", on_line=output_lines.append
            )
        )

    thread = threading.Thread(target=run)
    thread.start()
    time.sleep(3)  # let it start spinning
    runner.stop()
    thread.join(timeout=15)
    assert not thread.is_alive(), "Process did not terminate after stop()"
    assert result_code, "Process was not running when stop() was called"
