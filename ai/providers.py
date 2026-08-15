from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthMode(Enum):
    """Authentication mode for a provider."""
    NONE = "none"           # No auth needed (local providers like Ollama)
    API_KEY = "api_key"     # Standard API key in Authorization header
    TOKEN = "token"         # Bearer token (e.g., HF_TOKEN, DEEPINFRA_API_KEY)


@dataclass(frozen=True)
class ProviderEntry:
    """Describes a provider. Availability is determined at runtime by config + health."""
    id: str
    display_name: str
    base_url: str
    auth_mode: AuthMode
    env_var: str | None         # Environment variable name for credentials
    default_model: str
    priority: int               # Lower = tried first
    free_tier: bool = False     # Whether provider offers a free tier
    note: str = ""


# Verified providers only — 8 entries, no fabricated URLs
# Priority order: local first, then hosted by reliability/free-tier
PROVIDERS: list[ProviderEntry] = [
    ProviderEntry(
        id="ollama",
        display_name="Ollama Local",
        base_url="http://localhost:11434/v1",
        auth_mode=AuthMode.NONE,
        env_var=None,
        default_model="tinyllama:1b",
        priority=1,
        free_tier=True,
        note="Local model server — auto-installs on first use (7 MB), pulls model (~600 MB)"
    ),
    ProviderEntry(
        id="groq",
        display_name="Groq",
        base_url="https://api.groq.com/openai/v1",
        auth_mode=AuthMode.API_KEY,
        env_var="GROQ_API_KEY",
        default_model="llama-3.1-8b-instant",
        priority=2,
        free_tier=True,
        note="Fast inference, free tier 30 RPM"
    ),
    ProviderEntry(
        id="cerebras",
        display_name="Cerebras",
        base_url="https://api.cerebras.ai/v1",
        auth_mode=AuthMode.API_KEY,
        env_var="CEREBRAS_API_KEY",
        default_model="llama3.1-8b",
        priority=3,
        free_tier=True,
        note="Wafer-scale AI, free tier with generous limits"
    ),
    ProviderEntry(
        id="gemini",
        display_name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        auth_mode=AuthMode.API_KEY,
        env_var="GOOGLE_API_KEY",
        default_model="gemini-2-flash-exp",
        priority=4,
        free_tier=True,
        note="Google's latest, free tier available"
    ),
    ProviderEntry(
        id="mistral",
        display_name="Mistral",
        base_url="https://api.mistral.ai/v1",
        auth_mode=AuthMode.API_KEY,
        env_var="MISTRAL_API_KEY",
        default_model="mistral-small-latest",
        priority=5,
        free_tier=True,
        note="French AI, excellent free tier"
    ),
    ProviderEntry(
        id="deepinfra",
        display_name="DeepInfra",
        base_url="https://api.deepinfra.com/v1/openai",
        auth_mode=AuthMode.TOKEN,
        env_var="DEEPINFRA_API_KEY",
        default_model="meta-llama/Meta-Llama-3.1-8B-Instruct",
        priority=6,
        free_tier=True,
        note="OpenAI-compatible, concurrency-based limits"
    ),
    ProviderEntry(
        id="openrouter",
        display_name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        auth_mode=AuthMode.API_KEY,
        env_var="OPENROUTER_API_KEY",
        default_model="openrouter/free",
        priority=7,
        free_tier=True,
        note="Many models, free router 50 req/day, requires key"
    ),
    ProviderEntry(
        id="huggingface",
        display_name="HuggingFace",
        base_url="https://router.huggingface.co/v1",
        auth_mode=AuthMode.TOKEN,
        env_var="HF_TOKEN",
        default_model="openai/gpt-oss-120b:fastest",
        priority=8,
        free_tier=True,
        note="Inference Providers router, requires HF_TOKEN"
    ),
]


def get_providers_sorted() -> list[ProviderEntry]:
    """Return providers sorted by priority (lower number = higher priority)."""
    return sorted(PROVIDERS, key=lambda p: p.priority)


def get_providers_by_category(auth_mode: AuthMode | None = None) -> list[ProviderEntry]:
    """Filter providers by auth mode."""
    if auth_mode is None:
        return get_providers_sorted()
    return sorted(
        [p for p in PROVIDERS if p.auth_mode == auth_mode],
        key=lambda p: p.priority
    )


def get_provider_by_id(provider_id: str) -> ProviderEntry | None:
    """Find a provider by ID (case-insensitive)."""
    for p in PROVIDERS:
        if p.id.lower() == provider_id.lower():
            return p
    return None


def count_providers() -> dict[str, int]:
    """Count total providers and breakdown by auth mode."""
    counts: dict[str, int] = {"total": len(PROVIDERS)}
    for mode in AuthMode:
        counts[mode.value] = sum(1 for p in PROVIDERS if p.auth_mode == mode)
    return counts


def is_provider_configured(provider: ProviderEntry) -> bool:
    """Check if a provider has its required credentials configured."""
    if provider.auth_mode == AuthMode.NONE:
        return True
    if provider.env_var:
        import os
        return bool(os.environ.get(provider.env_var))
    return False


def get_configured_providers() -> list[ProviderEntry]:
    """Return only providers that have their credentials configured."""
    return [p for p in get_providers_sorted() if is_provider_configured(p)]


__all__ = [
    "AuthMode",
    "ProviderEntry",
    "PROVIDERS",
    "get_providers_sorted",
    "get_providers_by_category",
    "get_provider_by_id",
    "count_providers",
    "is_provider_configured",
    "get_configured_providers",
]