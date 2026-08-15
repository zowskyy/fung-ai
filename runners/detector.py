from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass


@dataclass
class Toolchain:
    name: str
    available: bool
    version: str = ""
    path: str = ""
    install_hint: str = ""


def _which(name: str) -> str | None:
    return shutil.which(name)


def _version(args: list[str]) -> str:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=15
        )
        first = (result.stdout or result.stderr).strip().splitlines()
        return first[0] if first else ""
    except Exception:
        return ""


def _python_executable() -> str | None:
    for name in ("python", "python3"):
        found = shutil.which(name)
        if found:
            return found
    # Fall back to the current interpreter only when not frozen, because a
    # PyInstaller bundle sets sys.executable to the bundled .exe (running it
    # again would re-launch the whole app).
    if not getattr(sys, "frozen", False):
        return sys.executable
    return None


def detect_python() -> Toolchain:
    path = _python_executable()
    return Toolchain(
        name="Python",
        available=path is not None,
        version=_version([path, "--version"]) if path else "",
        path=path or "",
        install_hint="Install Python from https://python.org",
    )


def detect_java() -> Toolchain:
    path = _which("java")
    return Toolchain(
        name="Java",
        available=path is not None,
        version=_version([path, "-version"]) if path else "",
        path=path or "",
        install_hint="Install JDK from https://adoptium.net",
    )


def detect_rust() -> Toolchain:
    path = _which("cargo")
    return Toolchain(
        name="Rust",
        available=path is not None,
        version=_version([path, "--version"]) if path else "",
        path=path or "",
        install_hint="Install Rust from https://rustup.rs",
    )


def detect_cpp() -> Toolchain:
    path = _which("g++") or _which("clang++") or _which("cl")
    return Toolchain(
        name="C++",
        available=path is not None,
        version=_version([path, "--version"]) if path else "",
        path=path or "",
        install_hint="Install Visual Studio Build Tools or MinGW",
    )


def detect_javascript() -> Toolchain:
    path = _which("node")
    return Toolchain(
        name="JavaScript",
        available=path is not None,
        version=_version([path, "--version"]) if path else "",
        path=path or "",
        install_hint="Install Node.js from https://nodejs.org",
    )


def detect_kotlin() -> Toolchain:
    path = _which("kotlinc")
    return Toolchain(
        name="Kotlin",
        available=path is not None,
        version=_version([path, "-version"]) if path else "",
        path=path or "",
        install_hint="Install Kotlin from https://kotlinlang.org/docs/command-line.html",
    )


def detect_all() -> list[Toolchain]:
    return [
        detect_python(),
        detect_java(),
        detect_rust(),
        detect_cpp(),
        detect_javascript(),
        detect_kotlin(),
    ]
