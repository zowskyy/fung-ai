"""Stress tests for RustRunner — exercise compile, run, panic, timeout, stop."""
from __future__ import annotations

import os
import shutil
import textwrap
import time

import pytest

from runners.rust_runner import RustRunner


CARGO = shutil.which("cargo")
rust_available = pytest.mark.skipif(
    CARGO is None, reason="cargo not installed"
)


def _make_rust_project(tmp_path: str) -> str:
    """Create a minimal Cargo project with a guessing game."""
    pkg = tmp_path
    os.makedirs(os.path.join(pkg, "src"))
    with open(os.path.join(pkg, "Cargo.toml"), "w") as f:
        f.write(textwrap.dedent("""\
            [package]
            name = "test_runner"
            version = "0.1.0"
            edition = "2021"

            [dependencies]
        """))
    with open(os.path.join(pkg, "src", "main.rs"), "w") as f:
        f.write(textwrap.dedent("""\
            use std::io::{self, Write};
            fn main() {
                println!("RustRunner OK");
                let mut buf = String::new();
                let _ = io::stdin().read_line(&mut buf);
            }
        """))
    return pkg


def _make_bad_rust_project(tmp_path: str) -> str:
    """Create a Rust project with a compile error."""
    pkg = tmp_path
    os.makedirs(os.path.join(pkg, "src"))
    with open(os.path.join(pkg, "Cargo.toml"), "w") as f:
        f.write(textwrap.dedent("""\
            [package]
            name = "bad_runner"
            version = "0.1.0"
            edition = "2021"
        """))
    with open(os.path.join(pkg, "src", "main.rs"), "w") as f:
        f.write("this is not valid rust code !!!\n")
    return pkg


def _make_panic_project(tmp_path: str) -> str:
    """Create a Rust project that panics at runtime."""
    pkg = tmp_path
    os.makedirs(os.path.join(pkg, "src"))
    with open(os.path.join(pkg, "Cargo.toml"), "w") as f:
        f.write(textwrap.dedent("""\
            [package]
            name = "panic_runner"
            version = "0.1.0"
            edition = "2021"
        """))
    with open(os.path.join(pkg, "src", "main.rs"), "w") as f:
        f.write("fn main() { panic!(\"intentional test panic\"); }\n")
    return pkg


def _make_infinite_loop_project(tmp_path: str) -> str:
    """Create a Rust project that loops forever."""
    pkg = tmp_path
    os.makedirs(os.path.join(pkg, "src"))
    with open(os.path.join(pkg, "Cargo.toml"), "w") as f:
        f.write(textwrap.dedent("""\
            [package]
            name = "infinite_runner"
            version = "0.1.0"
            edition = "2021"
        """))
    with open(os.path.join(pkg, "src", "main.rs"), "w") as f:
        f.write(textwrap.dedent("""\
            fn main() {
                loop { println!("spinning"); }
            }
        """))
    return pkg


@rust_available
class TestRustRunnerStress:

    def test_normal_program(self, tmp_path):
        """A well-formed Rust program should compile and exit cleanly."""
        pkg = _make_rust_project(str(tmp_path))
        runner = RustRunner()
        output_lines: list[str] = []
        code = runner.start_and_stream(
            cwd=pkg, script="src/main.rs", on_line=output_lines.append
        )
        assert code == 0
        joined = "\n".join(output_lines)
        assert "RustRunner OK" in joined

    def test_compile_error_captured(self, tmp_path):
        """A syntax error should return non-zero exit with stderr visible."""
        pkg = _make_bad_rust_project(str(tmp_path))
        runner = RustRunner()
        output_lines: list[str] = []
        code = runner.start_and_stream(
            cwd=pkg, script="src/main.rs", on_line=output_lines.append
        )
        assert code != 0
        joined = "\n".join(output_lines)
        assert "error" in joined.lower()

    def test_runtime_panic_captured(self, tmp_path):
        """A runtime panic should produce non-zero exit and visible panic output."""
        pkg = _make_panic_project(str(tmp_path))
        runner = RustRunner()
        output_lines: list[str] = []
        code = runner.start_and_stream(
            cwd=pkg, script="src/main.rs", on_line=output_lines.append
        )
        assert code != 0
        joined = "\n".join(output_lines)
        assert "panic" in joined.lower()

    def test_infinite_loop_terminated(self, tmp_path):
        """An infinite loop should be killable via stop() from another thread."""
        pkg = _make_infinite_loop_project(str(tmp_path))
        runner = RustRunner()

        import threading

        output_lines: list[str] = []
        result_code: list[int] = []

        def run():
            result_code.append(
                runner.start_and_stream(
                    cwd=pkg, script="src/main.rs", on_line=output_lines.append
                )
            )

        thread = threading.Thread(target=run)
        thread.start()
        time.sleep(5)  # let it compile and start spinning
        runner.stop()
        thread.join(timeout=15)
        assert not thread.is_alive(), "Process did not terminate after stop()"
        assert result_code, "Process was not running when stop() was called"
