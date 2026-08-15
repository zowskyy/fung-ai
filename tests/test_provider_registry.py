"""Tests for the provider registry — only verified providers, no fabricated URLs."""

from __future__ import annotations

import pytest

from ai.providers import (
    AuthMode,
    ProviderEntry,
    PROVIDERS,
    get_providers_sorted,
    get_providers_by_category,
    get_provider_by_id,
    count_providers,
)


class TestProviderRegistry:
    def test_exactly_eight_providers(self):
        assert len(PROVIDERS) == 8

    def test_all_required_fields_present(self):
        for p in PROVIDERS:
            assert p.id
            assert p.display_name
            assert p.base_url
            assert p.auth_mode in AuthMode
            assert p.default_model
            assert isinstance(p.priority, int)
            assert p.priority >= 1
            assert isinstance(p.free_tier, bool)

    def test_no_fabricated_domains(self):
        """None of the known fabricated domains should be present."""
        fabricated = {
            "blockrun.dev", "unclose.ai", "api.ovhcloud.com", "infermatic.dev",
            "brainop.ai", "petals.dev", "elyza.ai", "prem.ninja",
            "modeltxt.io", "nextpy.io", "antml.ai", "airgram.io",
        }
        for p in PROVIDERS:
            for bad in fabricated:
                assert bad not in p.base_url

    def test_priorities_unique_and_sequential(self):
        priorities = [p.priority for p in PROVIDERS]
        assert len(priorities) == len(set(priorities))
        assert sorted(priorities) == list(range(1, 9))

    def test_ollama_is_first_priority(self):
        assert PROVIDERS[0].id == "ollama"
        assert PROVIDERS[0].auth_mode == AuthMode.NONE

    def test_all_hosted_require_credentials(self):
        for p in PROVIDERS:
            if p.id != "ollama":
                assert p.auth_mode in (AuthMode.API_KEY, AuthMode.TOKEN)
                assert p.env_var is not None
                assert p.env_var.endswith("_KEY") or p.env_var == "HF_TOKEN"

    def test_specific_provider_entries(self):
        by_id = {p.id: p for p in PROVIDERS}

        assert by_id["groq"].base_url == "https://api.groq.com/openai/v1"
        assert by_id["groq"].auth_mode == AuthMode.API_KEY
        assert by_id["groq"].env_var == "GROQ_API_KEY"

        assert by_id["cerebras"].base_url == "https://api.cerebras.ai/v1"
        assert by_id["cerebras"].env_var == "CEREBRAS_API_KEY"

        assert by_id["gemini"].base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"
        assert by_id["gemini"].env_var == "GOOGLE_API_KEY"

        assert by_id["mistral"].base_url == "https://api.mistral.ai/v1"
        assert by_id["mistral"].env_var == "MISTRAL_API_KEY"

        assert by_id["deepinfra"].base_url == "https://api.deepinfra.com/v1/openai"
        assert by_id["deepinfra"].auth_mode == AuthMode.TOKEN
        assert by_id["deepinfra"].env_var == "DEEPINFRA_API_KEY"

        assert by_id["openrouter"].base_url == "https://openrouter.ai/api/v1"
        assert by_id["openrouter"].env_var == "OPENROUTER_API_KEY"
        assert by_id["openrouter"].default_model == "openrouter/free"

        assert by_id["huggingface"].base_url == "https://router.huggingface.co/v1"
        assert by_id["huggingface"].auth_mode == AuthMode.TOKEN
        assert by_id["huggingface"].env_var == "HF_TOKEN"
        assert ":fastest" in by_id["huggingface"].default_model


class TestProviderLookup:
    def test_get_providers_sorted_by_priority(self):
        sorted_providers = get_providers_sorted()
        assert [p.id for p in sorted_providers] == [
            "ollama", "groq", "cerebras", "gemini",
            "mistral", "deepinfra", "openrouter", "huggingface"
        ]

    def test_get_providers_by_auth_mode(self):
        none = get_providers_by_category(AuthMode.NONE)
        assert len(none) == 1
        assert none[0].id == "ollama"

        api_key = get_providers_by_category(AuthMode.API_KEY)
        assert len(api_key) == 5  # groq, cerebras, gemini, mistral, openrouter

    def test_get_provider_by_id_case_insensitive(self):
        p = get_provider_by_id("GROQ")
        assert p is not None
        assert p.id == "groq"

        p = get_provider_by_id("NonExistent")
        assert p is None


class TestProviderCount:
    def test_count_providers_structure(self):
        counts = count_providers()
        assert counts["total"] == 8
        assert "none" in counts
        assert "api_key" in counts
        assert "token" in counts
        assert counts["none"] == 1
        assert counts["api_key"] == 5  # groq, cerebras, gemini, mistral, openrouter
        assert counts["token"] == 2   # deepinfra, huggingface