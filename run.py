"""Run Creator, or learn how it works.

Usage:
    python run.py            Start the Creator app.
    python run.py --learn    Print a guided tour of the codebase.
    python run.py --test     Run the automated test suite.

The launcher sets up the Python environment on first run, so you can
double-click start.bat (Windows) or type `python run.py` and it just works.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PY = ROOT / ".venv" / "Scripts" / "python.exe"


def ensure_env() -> None:
    if VENV_PY.exists():
        return
    print("Setting up Creator for the first time...")
    subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
    subprocess.run(
        [str(VENV_PY), "-m", "pip", "install", "PySide6", "pytest", "--no-cache-dir", "--quiet"],
        check=True,
    )
    print("Environment ready.")


def learn() -> None:
    print("""
CREATOR - guided tour
=====================

The whole program lives in one folder. Here is the map:

  run.py                 THIS file. It launches the app, runs tests,
                         or shows this tour. Use it every time.

  main.py                The real entry point. It starts the window.

  app/                   The visual part (PySide6 desktop interface).
       main_window.py     The main window that switches between screens.
       widgets.py         Reusable form controls (text, colors, menus).
       screens/home.py    The start screen: create or open a project.
       screens/wizard.py  Step-by-step "make a new thing" flow.
       screens/editor.py  Edit, Run, Versions, and an Ask AI tab (with a
                          live "ideas" panel and an opt-in file-editing agent).

  core/                  The brain without a face (no GUI here).
      field_models.py    What a fill-in-the-blank field is, and validation.
      template_engine.py Turns templates + your answers into real files.

  sandbox/               Safe project storage.
      workspace.py       Where projects live on disk (your own folder).
      snapshots.py       Saves & restores versions of your work.

  repo/                  Version history using git, explained in plain words.
      git_manager.py     "Save a version", "Restore", "See what changed".

  runners/               Runs your creation like an expert.
       detector.py        Finds Python, Java, Rust, C++, JavaScript, Kotlin.
       python_runner.py   Runs the Python projects and streams their output.
       rust_runner.py     Runs Rust projects via `cargo run`.
       java_runner.py     Compiles and runs Java projects.
       cpp_runner.py      Compiles and runs C++ projects.
       kotlin_runner.py   Compiles and runs Kotlin projects.
       javascript_runner.py Runs JavaScript projects via Node.js.

  ai/                    OPTIONAL. Turn AI on to get help making things.
      backend.py         One interface that any AI provider can plug into.
      opencode.py        Adapter for the real opencode engine.
      python_shim.py     Adapter for any local/cloud OpenAI-style server.
      settings.py        Where your AI key is stored (never shared).

  templates/             The "kits" you start from.
       2d-platformer/     A jump-and-run game you can customize with no code.
       rust-number-guess/  Guess a number in Rust (no external deps).
       java-number-guess/  Guess a number in Java.
       cpp-number-guess/   Guess a number in C++.
       python-number-guess/  Guess a number in Python.
       javascript-number-guess/  Guess a number in JavaScript/Node.js.

  tests/                 Automated checks that keep everything working.

HOW TO LEARN BY DOING
---------------------
1.  python run.py                    -> open the app
2.  Click "Create a new project"     -> pick the platformer game
3.  Change the hero name and colors  -> click Create
4.  Go to the Run tab, click Run     -> your game window opens
5.  Go to the Versions tab           -> Save a version, restore it, diff it
6.  Go to the Ask AI tab             -> watch the "Ideas" panel fill in while
                                      the answer streams; tick "Let the AI edit
                                      my files" to let it change files (undoable
                                      via Versions). AI is optional and off until
                                      you connect a key or a local model.

Then open the files listed above in any editor and read them top to
bottom. Each one is short and does one job. The tests (tests/) show how
each piece is supposed to behave.
""")


def main() -> None:
    ensure_env()
    if "--learn" in sys.argv:
        learn()
        return
    if "--test" in sys.argv:
        basetemp = ROOT / ".pytest_tmp"
        raise SystemExit(
            subprocess.run(
                [
                    str(VENV_PY),
                    "-m",
                    "pytest",
                    str(ROOT / "tests"),
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    "--basetemp",
                    str(basetemp),
                ]
            ).returncode
        )
    if "--audit" in sys.argv:
        # Feedback-loop harness for the multi-instance ("pop up") bug.
        # See DEBUGGING_PROTOCOL.md and tools/audit_spawn.ps1.
        harness = ROOT / "tools" / "audit_spawn.ps1"
        args = sys.argv[2:]  # pass through -Exe/-Launches/-Iterations/...
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(harness), *args]
        raise SystemExit(subprocess.run(cmd).returncode)
    raise SystemExit(subprocess.run([str(VENV_PY), str(ROOT / "main.py"), *sys.argv[1:]]).returncode)


if __name__ == "__main__":
    main()
