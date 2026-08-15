"""Provider contract tests — every provider adapter must satisfy this behavioral contract.

These tests use mocked HTTP and do not require network access.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ai.providers import (
    AuthMode,
    ProviderEntry,
    get_providers_sorted,
)
from ai.python_shim import OpenAICompatBackend


# Contract test cases that every provider adapter must pass
CONTRACT_CASES = [
    ("valid_response", 200, {"choices": [{"delta": {"content": "hello"}}], "data": ["[DONE]"]}, "hello"),
    ("empty_response", 200, {"choices": [{"delta": {}}], "data": ["[DONE]"]}, ""),
    ("error_response", 200, {"error": {"message": "rate limited"}}, "RUNTIME_ERROR"),
    ("malformed_json", 200, "not json", "RUNTIME_ERROR"),
    ("http_401", 401, {"error": "unauthorized"}, "AUTH_ERROR"),
    ("http_404", 404, {"error": "not found"}, "ENDPOINT_ERROR"),
    ("http_429", 429, {"error": "rate limited", "retry_after": 30}, "RATE_LIMITED"),
    ("http_500", 500, {"error": "server error"}, "SERVER_ERROR"),
    ("http_503", 503, {"error": "unavailable"}, "SERVER_ERROR"),
]


@pytest.fixture
def mock_backend():
    """Create a mock OpenAICompatBackend with controllable urlopen."""
    with patch("ai.python_shim.urllib.request.urlopen") as mock_urlopen:
        backend = OpenAICompatBackend(
            base_url="https://api.test.com/v1",
            api_key="test-key",
            model="test-model",
        )
        yield backend, mock_urlopen


class TestOpenAICompatBackendContract:
    """Verify OpenAICompatBackend satisfies the provider contract."""

    def test_valid_response_returns_content(self, mock_backend):
        backend, mock_urlopen = mock_backend
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.__iter__ = MagicMock(return_value=iter([
            b'data: {"choices": [{"delta": {"content": "hello"}}]}\n',
            b"data: [DONE]\n",
        ]))
        mock_urlopen.return_value = mock_response

        result = backend.complete("system", [{"role": "user", "content": "test"}])
        assert result == "hello"

    def test_streaming_calls_on_delta(self, mock_backend):
        backend, mock_urlopen = mock_backend
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.__iter__ = MagicMock(return_value=iter([
            b'data: {"choices": [{"delta": {"content": "h"}}]}\n',
            b'data: {"choices": [{"delta": {"content": "i"}}]}\n',
            b"data: [DONE]\n",
        ]))
        mock_urlopen.return_value = mock_response

        chunks = []
        def on_delta(chunk):
            chunks.append(chunk)

        result = backend.complete("system", [{"role": "user", "content": "test"}], on_delta)
        assert result == "hi"
        assert chunks == ["h", "i"]

    def test_error_response_raises(self, mock_backend):
        backend, mock_urlopen = mock_backend
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.__iter__ = MagicMock(return_value=iter([
            b'data: {"error": {"message": "rate limited"}}\n',
            b"data: [DONE]\n",
        ]))
        mock_urlopen.return_value = mock_response

        with pytest.raises(RuntimeError, match="rate limited"):
            backend.complete("system", [{"role": "user", "content": "test"}])

    def test_empty_response_raises(self, mock_backend):
        backend, mock_urlopen = mock_backend
        mock_response = MagicMock()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_response.__iter__ = MagicMock(return_value=iter([
            b'data: {"choices": [{"delta": {}}]}\n',
            b"data: [DONE]\n",
        ]))
        mock_urlopen.return_value = mock_response

        with pytest.raises(RuntimeError, match="empty"):
            backend.complete("system", [{"role": "user", "content": "test"}])


class TestProviderEntryContract:
    """Verify each provider entry has required fields for the contract."""

    def test_all_providers_have_required_fields(self):
        for p in get_providers_sorted():
            assert p.id
            assert p.display_name
            assert p.base_url
            assert p.auth_mode in AuthMode
            assert p.env_var is None or isinstance(p.env_var, str)
            assert p.default_model
            assert isinstance(p.priority, int)
            assert p.priority >= 1

    def test_auth_mode_matches_env_var(self):
        for p in get_providers_sorted():
            if p.auth_mode == AuthMode.NONE:
                assert p.env_var is None
            else:
                assert p.env_var is not None
                assert len(p.env_var) > 0

    def test_ollama_is_only_none_auth(self):
        none_providers = [p for p in get_providers_sorted() if p.auth_mode == AuthMode.NONE]
        assert len(none_providers) == 1
        assert none_providers[0].id == "ollama"


class TestProviderFailureClassification:
    """Test that failure classification logic works correctly."""

    def test_classify_auth_failure(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("401 Unauthorized")) == "auth_failure"
        assert cb._classify_error(Exception("403 Forbidden")) == "auth_failure"
        assert cb._classify_error(Exception("unauthorized")) == "auth_failure"

    def test_classify_endpoint_not_found(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("404 Not Found")) == "endpoint_not_found"

    def test_classify_rate_limited(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("429 Too Many Requests")) == "rate_limited"
        assert cb._classify_error(Exception("rate limit exceeded")) == "rate_limited"

    def test_classify_server_errors(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("500 Internal Server Error")) == "server_error"
        assert cb._classify_error(Exception("502 Bad Gateway")) == "server_error"
        assert cb._classify_error(Exception("503 Service Unavailable")) == "server_error"
        assert cb._classify_error(Exception("504 Gateway Timeout")) == "server_error"

    def test_classify_timeout(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("timeout")) == "timeout"
        assert cb._classify_error(Exception("timed out")) == "timeout"

    def test_classify_dns_failure(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("dns lookup failed")) == "dns_failure"
        assert cb._classify_error(Exception("getaddrinfo failed")) == "dns_failure"

    def test_classify_connection_refused(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("connection refused")) == "connection_refused"
        assert cb._classify_error(Exception("connection reset")) == "connection_refused"

    def test_unknown_error(self):
        from ai.cycling import CyclingBackend
        cb = CyclingBackend()
        assert cb._classify_error(Exception("something weird")) == "unknown"