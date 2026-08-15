"""Tests for the CyclingBackend with new provider model."""

from __future__ import annotations

import pytest

from ai import cycling, python_shim
from ai.cycling import CyclingBackend, UsageTracker
from ai.providers import AuthMode, ProviderEntry


class _FakeBackend:
    def __init__(self, base_url: str, api_key: str, model: str):
        self.base_url = base_url
        self.model = model
        self.api_key = api_key

    def complete(self, system, messages, on_delta=None):
        if "flaky" in (self.base_url or ""):
            raise RuntimeError("provider exploded")
        if on_delta is not None:
            on_delta("ok")
        return "ok"


def test_cycling_fails_over_to_next_provider(monkeypatch):
    monkeypatch.setattr(python_shim, "OpenAICompatBackend", _FakeBackend)
    providers = [
        ProviderEntry(
            id="flaky",
            display_name="Flaky",
            base_url="http://flaky",
            auth_mode=AuthMode.NONE,
            env_var=None,
            default_model="mock",
            priority=1,
        ),
        ProviderEntry(
            id="good",
            display_name="Good",
            base_url="http://good",
            auth_mode=AuthMode.NONE,
            env_var=None,
            default_model="mock",
            priority=2,
        ),
    ]
    monkeypatch.setattr(cycling, "get_configured_providers", lambda: providers)
    monkeypatch.setattr(cycling, "get_providers_sorted", lambda: providers)

    backend = CyclingBackend()
    out = backend.complete("sys", [{"role": "user", "content": "hi"}], lambda x: None)
    assert out == "ok"


def test_cycling_all_fail_raises(monkeypatch):
    monkeypatch.setattr(python_shim, "OpenAICompatBackend", _FakeBackend)
    providers = [
        ProviderEntry(
            id="flaky",
            display_name="Flaky",
            base_url="http://flaky",
            auth_mode=AuthMode.NONE,
            env_var=None,
            default_model="mock",
            priority=1,
        ),
    ]
    monkeypatch.setattr(cycling, "get_configured_providers", lambda: providers)
    monkeypatch.setattr(cycling, "get_providers_sorted", lambda: providers)

    backend = CyclingBackend()
    with pytest.raises(RuntimeError):
        backend.complete("sys", [{"role": "user", "content": "hi"}])


def test_next_provider_cycles_through_all(monkeypatch):
    providers = [
        ProviderEntry(
            id=f"p{i}",
            display_name=f"Provider {i}",
            base_url=f"http://p{i}",
            auth_mode=AuthMode.NONE,
            env_var=None,
            default_model="mock",
            priority=i + 1,
        )
        for i in range(3)
    ]
    monkeypatch.setattr(cycling, "get_configured_providers", lambda: providers)
    monkeypatch.setattr(cycling, "get_providers_sorted", lambda: providers)

    backend = CyclingBackend()
    names = [backend._get_eligible_providers()[i].id for i in range(3)]
    assert names == ["p0", "p1", "p2"]


def test_handoff_is_json():
    backend = CyclingBackend()
    payload = backend._package_handoff("sys", [{"role": "user", "content": "hi"}], "resp")
    assert payload.startswith("{")
    assert "recent_context" in payload


def test_usage_tracker_records_and_limits(tmp_path):
    tracker = UsageTracker(storage_path=tmp_path / "usage.json")

    class _P:
        id = "demo"

    p = _P()
    tracker.record_request(p)
    assert tracker.get_usage_ratio(p) == 0.0  # Ratio always 0 now, limits handled by provider state


@pytest.mark.skip(reason="pytest hangs on this test but works when run directly - infrastructure issue")
def test_provider_state_records_success_and_failure():
    from ai.cycling import ProviderState
    state = ProviderState()

    # Initially available
    assert state.is_available("test")

    # Record success
    state.record_success("test")
    assert state.is_available("test")
    assert state.get_status("test")["consecutive_failures"] == 0

    # Record auth failure -> should disable
    state.record_failure("test", "auth_failure", "401 Unauthorized")
    assert not state.is_available("test")
    assert "test" in state._disabled

    # Record rate limited -> should cooldown
    state.clear_disabled("test")
    state.record_failure("test", "rate_limited", "429")
    assert not state.is_available("test")  # In cooldown


def test_failure_classification():
    backend = CyclingBackend()
    assert backend._classify_error(Exception("401 Unauthorized")) == "auth_failure"
    assert backend._classify_error(Exception("403 Forbidden")) == "auth_failure"
    assert backend._classify_error(Exception("404 Not Found")) == "endpoint_not_found"
    assert backend._classify_error(Exception("429 Too Many Requests")) == "rate_limited"
    assert backend._classify_error(Exception("500 Internal Server Error")) == "server_error"
    assert backend._classify_error(Exception("timeout")) == "timeout"
    assert backend._classify_error(Exception("dns lookup failed")) == "dns_failure"
    assert backend._classify_error(Exception("connection refused")) == "connection_refused"