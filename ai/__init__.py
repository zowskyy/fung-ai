from __future__ import annotations

from .backend import AIBackend
from .cycling import CyclingBackend
from .opencode import OpenCodeBackend
from .python_shim import OpenAICompatBackend
from .settings import load_credentials


_opencode_backend: OpenCodeBackend | None = None
_cycling_backend: CyclingBackend | None = None


def get_backend() -> AIBackend | None:
    global _opencode_backend, _cycling_backend
    creds = load_credentials()
    if not creds:
        return None
    mode = creds.get("mode")
    if mode == "opencode":
        if _opencode_backend is None:
            _opencode_backend = OpenCodeBackend(
                model=creds.get("opencode_model", "anthropic/claude-sonnet-4-5"),
                base_url=creds.get("opencode_base_url"),
            )
            _opencode_backend.start()
        return _opencode_backend if _opencode_backend.is_available() else None
    if mode == "openai_compat":
        return OpenAICompatBackend(
            base_url=creds.get("base_url", ""),
            api_key=creds.get("api_key", ""),
            model=creds.get("model", ""),
        )
    if mode == "cycling":
        if _cycling_backend is None:
            _cycling_backend = CyclingBackend()
        return _cycling_backend if _cycling_backend.is_available() else None
    return None


__all__ = [
    "AIBackend",
    "OpenCodeBackend",
    "OpenAICompatBackend",
    "CyclingBackend",
    "get_backend",
    "load_credentials",
]
