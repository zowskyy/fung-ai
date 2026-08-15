from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .backend import AIBackend
from .providers import (
    AuthMode,
    ProviderEntry,
    get_providers_sorted,
    is_provider_configured,
    get_configured_providers,
)
from .settings import AUTH_FILE
from .context_manager import (
    Conversation,
    ConversationPersistence,
    ContextWindowing,
    ProviderHealthChecker,
)


@dataclass
class UsageStats:
    rpm_used: int = 0
    rpd_used: int = 0
    last_rpm_reset: float = field(default_factory=time.time)
    last_rpd_reset: float = field(default_factory=time.time)


class UsageTracker:
    def __init__(self, storage_path: Path | None = None):
        self._stats: dict[str, UsageStats] = {}
        self._storage_path = storage_path or (AUTH_FILE.parent / "usage.json")
        self._load()

    def _load(self) -> None:
        try:
            if self._storage_path.exists():
                data = json.loads(self._storage_path.read_text(encoding="utf-8"))
                for provider_name, stats in data.items():
                    self._stats[provider_name] = UsageStats(
                        rpm_used=stats.get("rpm_used", 0),
                        rpd_used=stats.get("rpd_used", 0),
                        last_rpm_reset=stats.get("last_rpm_reset", time.time()),
                        last_rpd_reset=stats.get("last_rpd_reset", time.time()),
                    )
        except (OSError, json.JSONDecodeError):
            pass

    def _save(self) -> None:
        data = {}
        for name, stats in self._stats.items():
            data[name] = {
                "rpm_used": stats.rpm_used,
                "rpd_used": stats.rpd_used,
                "last_rpm_reset": stats.last_rpm_reset,
                "last_rpd_reset": stats.last_rpd_reset,
            }
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _reset_if_needed(self, stats: UsageStats, limit: int, window_seconds: int) -> None:
        now = time.time()
        if now - stats.last_rpm_reset >= 60:
            stats.rpm_used = 0
            stats.last_rpm_reset = now
        if now - stats.last_rpd_reset >= 86400:
            stats.rpd_used = 0
            stats.last_rpd_reset = now

    def record_request(self, provider: ProviderEntry) -> None:
        stats = self._stats.setdefault(provider.id, UsageStats())
        self._reset_if_needed(stats, 0, 60)
        self._reset_if_needed(stats, 0, 86400)
        stats.rpm_used += 1
        stats.rpd_used += 1
        self._save()

    def get_usage_ratio(self, provider: ProviderEntry) -> float:
        stats = self._stats.get(provider.id, UsageStats())
        self._reset_if_needed(stats, 0, 60)
        self._reset_if_needed(stats, 0, 86400)
        return 0.0  # Rate limits are now handled by provider health/cooldown


class ProviderState:
    """Tracks per-provider health state with thread-safe operations."""

    def __init__(self):
        self._lock = threading.Lock()
        self._cooldown_until: dict[str, float] = {}
        self._disabled: set[str] = set()
        self._consecutive_failures: dict[str, int] = {}
        self._last_error: dict[str, str] = {}

    def is_available(self, provider_id: str) -> bool:
        with self._lock:
            if provider_id in self._disabled:
                return False
            cooldown = self._cooldown_until.get(provider_id, 0)
            return time.time() >= cooldown

    def mark_attempting(self, provider_id: str) -> None:
        with self._lock:
            pass  # Could track in-flight requests if needed

    def record_success(self, provider_id: str) -> None:
        with self._lock:
            self._consecutive_failures[provider_id] = 0
            self._cooldown_until.pop(provider_id, None)
            self._last_error.pop(provider_id, None)

    def record_failure(self, provider_id: str, error_type: str, error_msg: str = "") -> None:
        """Record a failure and apply appropriate cooldown/disabling."""
        with self._lock:
            self._consecutive_failures[provider_id] = self._consecutive_failures.get(provider_id, 0) + 1
            self._last_error[provider_id] = f"{error_type}: {error_msg}"[:500]

            if error_type in ("auth_failure", "endpoint_not_found"):
                # Permanently disable until configuration changes
                self._disabled.add(provider_id)
            elif error_type == "rate_limited":
                # Cooldown for rate limit - will be extended by Retry-After parsing
                self._cooldown_until[provider_id] = time.time() + 60
            elif error_type in ("dns_failure", "connection_refused", "timeout", "server_error"):
                # Exponential backoff for transient failures
                failures = self._consecutive_failures[provider_id]
                backoff = min(30 * (2 ** (failures - 1)), 300)  # 30s, 60s, 120s, max 300s
                self._cooldown_until[provider_id] = time.time() + backoff
            else:
                # Unknown error - moderate cooldown
                self._cooldown_until[provider_id] = time.time() + 60

    def clear_disabled(self, provider_id: str) -> None:
        """Re-enable a provider (e.g., after env var changes)."""
        with self._lock:
            self._disabled.discard(provider_id)
            self._cooldown_until.pop(provider_id, None)
            self._consecutive_failures.pop(provider_id, None)
            self._last_error.pop(provider_id, None)

    def get_status(self, provider_id: str) -> dict:
        with self._lock:
            return {
                "available": self.is_available(provider_id),
                "disabled": provider_id in self._disabled,
                "cooldown_until": self._cooldown_until.get(provider_id, 0),
                "consecutive_failures": self._consecutive_failures.get(provider_id, 0),
                "last_error": self._last_error.get(provider_id, ""),
            }


class CyclingBackend(AIBackend):
    name = "Cycling"

    def __init__(self) -> None:
        self._all_providers = get_providers_sorted()
        self._tracker = UsageTracker()
        self._provider_state = ProviderState()
        self._lock = threading.Lock()
        self._current_index = self._load_cycle_index()
        self._handoff_context: str | None = None

        # Conversation persistence
        self._persistence = ConversationPersistence()
        self._context_windowing = ContextWindowing()
        self._health_checker = ProviderHealthChecker()
        self._current_conversation: Conversation | None = None

    def _load_cycle_index(self) -> int:
        try:
            if AUTH_FILE.exists():
                data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
                return data.get("cycle_index", 0)
        except (OSError, json.JSONDecodeError):
            pass
        return 0

    def _save_cycle_index(self, index: int) -> None:
        try:
            data = {}
            if AUTH_FILE.exists():
                data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
            data["cycle_index"] = index
            AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
            AUTH_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except (OSError, json.JSONDecodeError):
            pass

    def start_conversation(self, conversation_id: str | None = None) -> str:
        if conversation_id:
            conv = self._persistence.load(conversation_id)
            if conv:
                self._current_conversation = conv
                return conversation_id
        new_id = str(uuid.uuid4())[:8]
        self._current_conversation = Conversation(id=new_id)
        return new_id

    def get_current_conversation_id(self) -> str | None:
        return self._current_conversation.id if self._current_conversation else None

    def _get_eligible_providers(self) -> list[ProviderEntry]:
        """Return only providers that are configured AND healthy (not in cooldown/disabled)."""
        configured = get_configured_providers()
        eligible = []
        for provider in configured:
            if self._provider_state.is_available(provider.id):
                eligible.append(provider)
        return eligible

    def _select_provider(self) -> ProviderEntry | None:
        """Select next provider in priority order, skipping unavailable ones."""
        eligible = self._get_eligible_providers()
        if not eligible:
            return None
        if self._current_index >= len(eligible):
            self._current_index = 0
        provider = eligible[self._current_index]
        self._current_index = (self._current_index + 1) % len(eligible)
        self._save_cycle_index(self._current_index)
        return provider

    def complete(
        self,
        system: str,
        messages: list[dict],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        """Complete a request with automatic provider cycling and failure handling."""
        from .python_shim import OpenAICompatBackend

        if not self._current_conversation:
            self.start_conversation()

        for msg in messages:
            if msg["role"] == "user":
                self._current_conversation.add_message("user", msg["content"])

        attempted: set[str] = set()
        last_error: Exception | None = None
        last_error_type: str = "unknown"

        # Try each eligible provider
        for _ in range(len(self._all_providers) + 1):
            provider = self._select_provider()
            if provider is None:
                break
            if provider.id in attempted:
                continue
            attempted.add(provider.id)

            windowed_messages: list[dict] = []
            try:
                windowed_messages = self._context_windowing.window_for_provider(
                    self._current_conversation, provider.id
                )
                full_system = system
                if self._handoff_context:
                    full_system = (
                        f"{system}\n\n--- Context handed off from previous provider ---\n"
                        f"{self._handoff_context}"
                    )
                backend = OpenAICompatBackend(
                    base_url=provider.base_url,
                    api_key=os.environ.get(provider.env_var or "", ""),
                    model=provider.default_model,
                )
                response = backend.complete(full_system, windowed_messages, on_delta)
            except Exception as exc:
                last_error = exc
                error_type = self._classify_error(exc)
                last_error_type = error_type
                self._health_checker.mark_checked(provider.id, False)
                self._provider_state.record_failure(provider.id, error_type, str(exc))
                self._handoff_context = self._package_handoff(
                    system, windowed_messages, ""
                )
                continue

            # Success
            self._tracker.record_request(provider)
            self._current_conversation.add_message("assistant", response)
            self._persistence.save(self._current_conversation)
            self._provider_state.record_success(provider.id)
            self._handoff_context = self._package_handoff(
                system, windowed_messages, response
            )
            return response

        # All providers failed
        raise RuntimeError(
            f"All available AI providers failed. Last error ({last_error_type}): {last_error}"
        )

    def _classify_error(self, exc: Exception) -> str:
        """Classify an exception into a failure type for appropriate handling."""
        msg = str(exc).lower()

        # Check for HTTP status codes in error message
        if "401" in msg or "403" in msg or "unauthorized" in msg or "forbidden" in msg:
            return "auth_failure"
        if "404" in msg or "not found" in msg:
            return "endpoint_not_found"
        if "429" in msg or "rate limit" in msg or "too many requests" in msg:
            return "rate_limited"
        if "500" in msg or "502" in msg or "503" in msg or "504" in msg or "server error" in msg:
            return "server_error"
        if "timeout" in msg or "timed out" in msg:
            return "timeout"
        if "dns" in msg or "name resolution" in msg or "getaddrinfo" in msg:
            return "dns_failure"
        if "connection refused" in msg or "connection reset" in msg:
            return "connection_refused"
        if "ssl" in msg or "certificate" in msg:
            return "ssl_error"

        return "unknown"

    def _package_handoff(self, system: str, messages: list[dict], response: str) -> str:
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        handoff = {
            "system_prompt": system,
            "recent_context": recent_messages,
            "last_response": response[-2000:] if len(response) > 2000 else response,
            "handoff_timestamp": time.time(),
        }
        return json.dumps(handoff, indent=2)

    def is_available(self) -> bool:
        return len(self._get_eligible_providers()) > 0

    def get_provider_status(self, provider_id: str) -> dict:
        """Get health status for a specific provider."""
        return self._provider_state.get_status(provider_id)

    def get_all_status(self) -> dict[str, dict]:
        """Get health status for all providers."""
        return {p.id: self._provider_state.get_status(p.id) for p in self._all_providers}

    def refresh_provider_eligibility(self) -> None:
        """Call when environment variables may have changed."""
        for provider in self._all_providers:
            if is_provider_configured(provider):
                self._provider_state.clear_disabled(provider.id)


__all__ = [
    "UsageTracker",
    "CyclingBackend",
]