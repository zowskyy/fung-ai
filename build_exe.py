"""Build a standalone Creator executable with PyInstaller.

Run via ``python build_exe.py`` (or ``python build.py --exe``). The result is a
``Creator/`` folder in ``dist/`` containing ``Creator.exe`` (plus its DLLs) that
needs no Python install.

We use ``--onedir`` (not ``--onefile``) on purpose: ``--onefile`` spends several
seconds extracting to a temp dir before the app starts, so rapid double-clicks
each spin up their own full extraction and look like the app "pops up" many
times. ``--onedir`` launches in ~1s, so the single-instance guard in
``main.py`` takes effect almost immediately.

Templates are bundled so the frozen app finds them via ``app_root()`` ->
``sys.executable``'s parent folder (or ``sys._MEIPASS`` when frozen).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from PyInstaller.__main__ import run as pyinstaller_run

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
DIST = ROOT / "dist"
BUILD = ROOT / "build"

# Keep build artifacts out of the final binary's working dir.
shutil.rmtree(BUILD, ignore_errors=True)
shutil.rmtree(DIST, ignore_errors=True)

HIDDEN = [
    "ai.opencode",
    "ai.python_shim",
    "ai.cycling",
    "ai.providers",
    "core.template_engine",
    "core.field_models",
    "repo.git_manager",
    "runners.detector",
    "runners.python_runner",
    "runners.java_runner",
    "runners.rust_runner",
    "runners.cpp_runner",
    "runners.kotlin_runner",
    "runners.javascript_runner",
    "sandbox.workspace",
    "sandbox.snapshots",
    "app.main_window",
    "app.screens.home",
    "app.screens.wizard",
    "app.screens.editor",
    "app.widgets.sidebar",
    "app.widgets.markdown",
    "app.widgets.diff_view",
    "app.widgets.tool_view",
    "app.widgets.context_panel",
    "app.notifications",
    "app.paths",
    "app.utils",
]

cmd: list[str] = [
    str(ROOT / "main.py"),
    "--name", "Creator",
    "--onedir",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--add-data", f"{TEMPLATES}:templates",
    # Exclude problematic PySide6 modules that Creator doesn't use
    "--exclude-module", "PySide6.QtMultimedia",
    "--exclude-module", "PySide6.QtNetworkAuth",
    "--exclude-module", "PySide6.QtWebEngineCore",
]
for module in HIDDEN:
    cmd += ["--hidden-import", module]

if __name__ == "__main__":
    pyinstaller_run(cmd)
    print(f"\nBuilt standalone executable at {DIST / 'Creator' / 'Creator.exe'}")
