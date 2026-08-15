from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from runners.python_runner import PythonRunner, find_python


def test_find_python_uses_current_interpreter_when_not_frozen():
    # The running interpreter is guaranteed valid; we must not pick up the
    # Windows Store `python.exe` app-execution alias (exit code 9009).
    assert find_python() == sys.executable


def test_runs_user_script_and_streams_output(tmp_path):
    script = tmp_path / "demo.py"
    script.write_text("print('hello-fungai')\n", encoding="utf-8")

    runner = PythonRunner()
    lines: list[str] = []
    code = runner.start_and_stream(tmp_path, "demo.py", lines.append)

    assert code == 0
    assert any("hello-fungai" in line for line in lines)


def test_stop_terminates_running_process():
    import shutil
    import tempfile
    import threading
    import time

    tmp = Path(tempfile.mkdtemp(prefix="creator-stop-"))
    try:
        script = tmp / "loop.py"
        script.write_text("import time\nwhile True:\n    time.sleep(0.1)\n", encoding="utf-8")

        runner = PythonRunner()
        result: dict = {}

        def _run():
            result["code"] = runner.start_and_stream(tmp, "loop.py", lambda _: None)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        # Wait until start_and_stream has actually spawned the subprocess.
        for _ in range(100):
            if runner._process is not None:
                break
            time.sleep(0.05)
        runner.stop()
        thread.join(timeout=10)
        assert not thread.is_alive()
    finally:
        time.sleep(0.5)
        shutil.rmtree(tmp, ignore_errors=True)
