"""Tests for provider configuration and eligibility logic."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from ai.providers import (
    AuthMode,
    ProviderEntry,
    PROVIDERS,
    is_provider_configured,
    get_configured_providers,
    get_providers_sorted,
)


class TestProviderConfiguration:
    def test_unconfigured_hosted_provider(self):
        """A hosted provider without its env var should not be configured."""
        provider = next(p for p in PROVIDERS if p.id == "groq")
        with patch.dict(os.environ, {}, clear=True):
            assert is_provider_configured(provider) is False

    def test_configured_hosted_provider(self):
        """A hosted provider with its env var should be configured."""
        provider = next(p for p in PROVIDERS if p.id == "groq")
        with patch.dict(os.environ, {"GROQ_API_KEY": "test-key"}):
            assert is_provider_configured(provider) is True

    def test_ollama_always_configured(self):
        """Ollama (auth_mode=NONE) should always be configured."""
        provider = next(p for p in PROVIDERS if p.id == "ollama")
        with patch.dict(os.environ, {}, clear=True):
            assert is_provider_configured(provider) is True

    def test_empty_env_var_not_configured(self):
        """An empty env var should not count as configured."""
        provider = next(p for p in PROVIDERS if p.id == "groq")
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
            assert is_provider_configured(provider) is False

    def test_get_configured_providers_only_returns_configured(self):
        """get_configured_providers should filter by configuration."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "test", "CEREBRAS_API_KEY": "test"}):
            configured = get_configured_providers()
            ids = {p.id for p in configured}
            assert "ollama" in ids
            assert "groq" in ids
            assert "cerebras" in ids
            assert "gemini" not in ids
            assert "mistral" not in ids
            assert "deepinfra" not in ids
            assert "openrouter" not in ids
            assert "huggingface" not in ids


class TestProviderEntryValidation:
    def test_all_env_vars_are_sensible(self):
        for p in PROVIDERS:
            if p.auth_mode != AuthMode.NONE:
                assert p.env_var
                assert p.env_var.isupper()
                assert "_" in p.env_var or p.env_var == "HF_TOKEN"

    def test_no_hardcoded_quotas(self):
        """Providers should not have hardcoded quota numbers in their definitions."""
        for p in PROVIDERS:
            # The only quota-related field is free_tier (bool)
            assert not hasattr(p, "rpm_limit")
            assert not hasattr(p, "rpd_limit")
            assert not hasattr(p, "quota")