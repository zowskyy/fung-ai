"""Live integration tests for providers — opt-in via pytest -m live.

These tests REQUIRE valid API credentials in environment variables.
They are skipped by default and only run with: pytest -m live
"""

from __future__ import annotations

import os
import pytest

from ai.providers import get_providers_sorted, is_provider_configured
from ai.python_shim import OpenAICompatBackend


# Mark all tests in this module as live
pytestmark = pytest.mark.live


class TestLiveProviders:
    """Test each configured provider with a real API call."""

    @pytest.fixture(autouse=True)
    def check_credentials(self):
        """Skip if no providers are configured."""
        configured = [p for p in get_providers_sorted() if is_provider_configured(p)]
        if not configured:
            pytest.skip("No provider credentials configured")

    def test_ollama_if_running(self):
        """Test Ollama if it's running locally."""
        from ai.llm_setup import is_ollama_running, get_ollama_status

        if not is_ollama_running():
            pytest.skip("Ollama not running")

        status = get_ollama_status()
        if not status.get("models"):
            pytest.skip("No Ollama models pulled")

        model = status["models"][0]
        backend = OpenAICompatBackend(
            base_url="http://localhost:11434/v1",
            api_key="",
            model=model,
        )
        try:
            result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
            assert result
            assert len(result) > 0
        except Exception as e:
            pytest.fail(f"Ollama request failed: {e}")

    def test_groq_if_configured(self):
        """Test Groq if GROQ_API_KEY is set."""
        if not os.environ.get("GROQ_API_KEY"):
            pytest.skip("GROQ_API_KEY not set")

        backend = OpenAICompatBackend(
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ["GROQ_API_KEY"],
            model="llama-3.1-8b-instant",
        )
        result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
        assert result
        assert len(result) > 0

    def test_cerebras_if_configured(self):
        """Test Cerebras if CEREBRAS_API_KEY is set."""
        if not os.environ.get("CEREBRAS_API_KEY"):
            pytest.skip("CEREBRAS_API_KEY not set")

        backend = OpenAICompatBackend(
            base_url="https://api.cerebras.ai/v1",
            api_key=os.environ["CEREBRAS_API_KEY"],
            model="llama3.1-8b",
        )
        result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
        assert result
        assert len(result) > 0

    def test_gemini_if_configured(self):
        """Test Gemini if GOOGLE_API_KEY is set."""
        if not os.environ.get("GOOGLE_API_KEY"):
            pytest.skip("GOOGLE_API_KEY not set")

        backend = OpenAICompatBackend(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.environ["GOOGLE_API_KEY"],
            model="gemini-2-flash-exp",
        )
        result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
        assert result
        assert len(result) > 0

    def test_mistral_if_configured(self):
        """Test Mistral if MISTRAL_API_KEY is set."""
        if not os.environ.get("MISTRAL_API_KEY"):
            pytest.skip("MISTRAL_API_KEY not set")

        backend = OpenAICompatBackend(
            base_url="https://api.mistral.ai/v1",
            api_key=os.environ["MISTRAL_API_KEY"],
            model="mistral-small-latest",
        )
        result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
        assert result
        assert len(result) > 0

    def test_deepinfra_if_configured(self):
        """Test DeepInfra if DEEPINFRA_API_KEY is set."""
        if not os.environ.get("DEEPINFRA_API_KEY"):
            pytest.skip("DEEPINFRA_API_KEY not set")

        backend = OpenAICompatBackend(
            base_url="https://api.deepinfra.com/v1/openai",
            api_key=os.environ["DEEPINFRA_API_KEY"],
            model="meta-llama/Meta-Llama-3.1-8B-Instruct",
        )
        result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
        assert result
        assert len(result) > 0

    def test_openrouter_if_configured(self):
        """Test OpenRouter if OPENROUTER_API_KEY is set."""
        if not os.environ.get("OPENROUTER_API_KEY"):
            pytest.skip("OPENROUTER_API_KEY not set")

        backend = OpenAICompatBackend(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            model="openrouter/free",
        )
        result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
        assert result
        assert len(result) > 0

    def test_huggingface_if_configured(self):
        """Test HuggingFace if HF_TOKEN is set."""
        if not os.environ.get("HF_TOKEN"):
            pytest.skip("HF_TOKEN not set")

        backend = OpenAICompatBackend(
            base_url="https://router.huggingface.co/v1",
            api_key=os.environ["HF_TOKEN"],
            model="openai/gpt-oss-120b:fastest",
        )
        result = backend.complete("Say hello", [{"role": "user", "content": "Hi"}])
        assert result
        assert len(result) > 0


class TestLiveCyclingBackend:
    """Test the full CyclingBackend with live providers."""

    def test_cycling_failover(self):
        """Verify cycling backend tries providers in order."""
        from ai.cycling import CyclingBackend

        # Configure at least 2 providers
        configured = [p for p in get_providers_sorted() if is_provider_configured(p)]
        if len(configured) < 2:
            pytest.skip("Need at least 2 configured providers for failover test")

        backend = CyclingBackend()
        result = backend.complete(
            "You are a helpful assistant.",
            [{"role": "user", "content": "Say 'test passed'"}],
        )
        assert result
        assert "test passed" in result.lower()


# Convenience function to run a quick live check manually
if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v", "-m", "live"]))