"""On-demand local LLM setup — Ollama and GGUF fallback.

Three provider tiers:
  1. Cloud free (OpenRouter, etc.) — zero local footprint, needs internet
  2. Ollama — 7 MB exe download, ~600 MB model, truly local
  3. Embedded GGUF — llama-cpp-python + ~700 MB model, no Ollama needed

All downloads are on-demand and cache in ~/.creator/ollama/ or ~/.creator/models/.
The Creator installer itself is never bloated.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Callable

OLLAMA_URL = "https://ollama.com/download/ollama-windows-amd64.exe"
OLLAMA_DIR = Path.home() / ".creator" / "ollama"
OLLAMA_EXE = OLLAMA_DIR / "ollama.exe"

GGUF_MODEL_URL = (
    "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    "/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"
)
GGUF_DIR = Path.home() / ".creator" / "models"
GGUF_FILE = GGUF_DIR / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

DEFAULT_OLLAMA_MODEL = "tinyllama:1b"
OLLAMA_PORT = 11434


def is_ollama_installed() -> bool:
    """Check if Ollama is available on PATH or in our cache."""
    if OLLAMA_EXE.exists():
        return True
    return shutil.which("ollama") is not None


def is_ollama_running() -> bool:
    """Check if an Ollama server is reachable."""
    try:
        url = f"http://localhost:{OLLAMA_PORT}/api/tags"
        with urllib.request.urlopen(url, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def install_ollama(on_progress: Callable[[str], None] | None = None) -> bool:
    """Download the Ollama standalone exe to ~/.creator/ollama/.

    Returns True on success. Does nothing if already installed.
    """
    if is_ollama_installed():
        return True
    OLLAMA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if on_progress:
            on_progress("Downloading Ollama (~7 MB)...")
        urllib.request.urlretrieve(OLLAMA_URL, str(OLLAMA_EXE))
        OLLAMA_EXE.chmod(OLLAMA_EXE.stat().st_mode | stat.S_IEXEC)
        if on_progress:
            on_progress("Ollama installed.")
        return True
    except Exception as exc:
        if on_progress:
            on_progress(f"Ollama install failed: {exc}")
        return False


def pull_ollama_model(
    model: str = DEFAULT_OLLAMA_MODEL,
    on_progress: Callable[[str], None] | None = None,
) -> bool:
    """Pull a model via Ollama. Starts the server if needed. Returns True on success."""
    ollama_bin = _find_ollama_binary()
    if not ollama_bin:
        return False
    if on_progress:
        on_progress(f"Pulling {model} (may take a minute)...")
    try:
        result = subprocess.run(
            [str(ollama_bin), "pull", model],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            if on_progress:
                on_progress(f"Model {model} ready.")
            return True
        if on_progress:
            on_progress(f"Pull failed: {result.stderr[:200]}")
        return False
    except Exception as exc:
        if on_progress:
            on_progress(f"Pull error: {exc}")
        return False


def start_ollama_server() -> bool:
    """Start the Ollama server as a background process.

    Uses ``ollama serve`` (the embedded server binary) so no separate install
    is needed. The process is daemonized so it dies when the parent exits.
    """
    ollama_bin = _find_ollama_binary()
    if not ollama_bin:
        return False
    if is_ollama_running():
        return True
    try:
        kwargs: dict = dict(
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0,
        )
        if sys.platform == "win32":
            kwargs["creationflags"] = (
                getattr(subprocess, "CREATE_NO_WINDOW", 0)
                | getattr(subprocess, "DETACHED_PROCESS", 0)
            )
        subprocess.Popen(
            [str(ollama_bin), "serve"],
            stdin=subprocess.DEVNULL,
            **kwargs,
        )
        # Wait briefly for the server to come up
        import time
        for _ in range(10):
            time.sleep(0.5)
            if is_ollama_running():
                return True
        return is_ollama_running()
    except Exception:
        return False


def get_ollama_status() -> dict:
    """Return status dict for Ollama."""
    installed = is_ollama_installed()
    running = is_ollama_running() if installed else False
    models: list[str] = []
    if running:
        try:
            url = f"http://localhost:{OLLAMA_PORT}/api/tags"
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
        except Exception:
            pass
    return {
        "installed": installed,
        "running": running,
        "models": models,
        "binary": str(_find_ollama_binary() or ""),
    }


def _find_ollama_binary() -> Path | None:
    if OLLAMA_EXE.exists():
        return OLLAMA_EXE
    which = shutil.which("ollama")
    if which:
        return Path(which)
    return None


# ---------------------------------------------------------------------------
# GGUF fallback (embedded, no Ollama needed)
# ---------------------------------------------------------------------------

def is_gguf_available() -> bool:
    """Check if the bundled GGUF model file exists locally."""
    return GGUF_FILE.exists()


def download_gguf_model(on_progress: Callable[[str], None] | None = None) -> bool:
    """Download a tiny GGUF model from HuggingFace. ~700 MB, one-time."""
    if GGUF_FILE.exists():
        return True
    GGUF_DIR.mkdir(parents=True, exist_ok=True)
    tmp = GGUF_DIR / (GGUF_FILE.name + ".tmp")
    try:
        if on_progress:
            on_progress("Downloading tiny model (~700 MB, one-time)...")
        req = urllib.request.Request(GGUF_MODEL_URL)
        with urllib.request.urlopen(req, timeout=600) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 256
            with open(tmp, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if on_progress and total > 0:
                        pct = int(downloaded * 100 / total)
                        on_progress(f"Downloading model... {pct}%")
        tmp.rename(GGUF_FILE)
        if on_progress:
            on_progress("Model downloaded.")
        return True
    except Exception as exc:
        if on_progress:
            on_progress(f"Model download failed: {exc}")
        tmp.unlink(missing_ok=True)
        return False


def get_gguf_status() -> dict:
    """Return status dict for embedded GGUF."""
    return {
        "available": is_gguf_available(),
        "path": str(GGUF_FILE) if GGUF_FILE.exists() else "",
        "model_url": GGUF_MODEL_URL,
        "size_mb": round(GGUF_FILE.stat().st_size / 1048576, 1) if GGUF_FILE.exists() else 0,
    }


__all__ = [
    "is_ollama_installed",
    "is_ollama_running",
    "install_ollama",
    "pull_ollama_model",
    "get_ollama_status",
    "is_gguf_available",
    "download_gguf_model",
    "get_gguf_status",
    "OLLAMA_DIR",
    "OLLAMA_EXE",
    "GGUF_DIR",
    "GGUF_FILE",
    "DEFAULT_OLLAMA_MODEL",
]
