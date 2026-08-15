from __future__ import annotations

from .backend import AIBackend
from .cycling import CyclingBackend
from .opencode import OpenCodeBackend
from .python_shim import OpenAICompatBackend
from .settings import load_credentials, set_credentials


_opencode_backend: OpenCodeBackend | None = None
_cycling_backend: CyclingBackend | None = None


def get_backend() -> AIBackend | None:
    """Return the active AI backend.

    On a fresh install with no auth.json, we auto-initialize cycling mode so
    the app works immediately out of the box — no configuration required.
    """
    global _opencode_backend, _cycling_backend
    creds = load_credentials()

    # Fresh install: no config at all — auto-start cycling with no-key providers
    if not creds:
        set_credentials("cycling")
        creds = {"mode": "cycling"}

    mode = creds.get("mode", "cycling")

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

    # Default: cycling mode (fresh install or explicit)
    if _cycling_backend is None:
        _cycling_backend = CyclingBackend()
    # Always return the backend — is_available check happens per-request
    return _cycling_backend


__all__ = [
    "AIBackend",
    "OpenCodeBackend",
    "OpenAICompatBackend",
    "CyclingBackend",
    "get_backend",
    "load_credentials",
]
