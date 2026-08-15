from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .backend import AIBackend
from .providers import ModelProvider, get_providers_sorted
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

    def record_request(self, provider: ModelProvider) -> None:
        stats = self._stats.setdefault(provider.name, UsageStats())
        self._reset_if_needed(stats, provider.rpm_limit, 60)
        self._reset_if_needed(stats, provider.rpd_limit, 86400)
        stats.rpm_used += 1
        stats.rpd_used += 1
        self._save()

    def get_usage_ratio(self, provider: ModelProvider) -> float:
        stats = self._stats.get(provider.name, UsageStats())
        self._reset_if_needed(stats, provider.rpm_limit, 60)
        self._reset_if_needed(stats, provider.rpd_limit, 86400)
        rpm_ratio = stats.rpm_used / provider.rpm_limit if provider.rpm_limit > 0 else 0
        rpd_ratio = stats.rpd_used / provider.rpd_limit if provider.rpd_limit > 0 else 0
        return max(rpm_ratio, rpd_ratio)

    def is_at_limit(self, provider: ModelProvider, threshold: float = 0.8) -> bool:
        return self.get_usage_ratio(provider) >= threshold


class CyclingBackend(AIBackend):
    name = "Cycling"

    def __init__(self) -> None:
        self._providers = get_providers_sorted()
        self._tracker = UsageTracker()
        self._current_index = self._load_cycle_index()
        self._handoff_context: str | None = None

        # Conversation persistence
        self._persistence = ConversationPersistence()
        self._context_windowing = ContextWindowing()
        self._health_checker = ProviderHealthChecker()
        self._current_conversation: Conversation | None = None

    def start_conversation(self, conversation_id: str | None = None) -> str:
        """Start or resume a conversation.

        Args:
            conversation_id: Resume existing conversation, or None for new

        Returns:
            Conversation ID (newly generated or provided)
        """
        if conversation_id:
            # Try to load existing conversation
            conv = self._persistence.load(conversation_id)
            if conv:
                self._current_conversation = conv
                return conversation_id

        # Create new conversation
        new_id = str(uuid.uuid4())[:8]
        self._current_conversation = Conversation(id=new_id)
        return new_id

    def get_current_conversation_id(self) -> str | None:
        """Get ID of current conversation."""
        return self._current_conversation.id if self._current_conversation else None

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

    def _get_available_providers(self) -> list[ModelProvider]:
        available = []
        for provider in self._providers:
            if provider.requires_key:
                key = os.environ.get(provider.key_env_var or "")
                if not key:
                    continue
            if not self._tracker.is_at_limit(provider):
                available.append(provider)
        return available

    def _get_next_provider(self) -> ModelProvider | None:
        available = self._get_available_providers()
        if not available:
            return None
        if self._current_index >= len(available):
            self._current_index = 0
        provider = available[self._current_index]
        self._current_index = (self._current_index + 1) % len(available)
        self._save_cycle_index(self._current_index)
        return provider

    def complete(
        self,
        system: str,
        messages: list[dict],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        """Complete a request with automatic provider cycling and context preservation.

        Args:
            system: System prompt
            messages: Chat messages (list of {"role": "user"|"assistant", "content": str})
            on_delta: Optional callback for streaming chunks

        Returns:
            Response text

        Raises:
            RuntimeError: If no providers available
        """
        # Ensure we have a conversation
        if not self._current_conversation:
            self.start_conversation()

        # Add user messages to conversation
        for msg in messages:
            if msg["role"] == "user":
                self._current_conversation.add_message("user", msg["content"])

        # Select provider with smart failover
        provider = self._get_next_provider()
        if not provider:
            raise RuntimeError("No available providers (all at rate limits or missing keys)")

        # Use context windowing for this provider
        windowed_messages = self._context_windowing.window_for_provider(
            self._current_conversation, provider.name
        )

        from .python_shim import OpenAICompatBackend

        backend = OpenAICompatBackend(
            base_url=provider.base_url,
            api_key=os.environ.get(provider.key_env_var or "", ""),
            model=provider.models[0],
        )

        full_system = system
        if self._handoff_context:
            full_system = f"{system}\n\n--- Context handed off from previous provider ---\n{self._handoff_context}"

        try:
            response = backend.complete(full_system, windowed_messages, on_delta)
            self._tracker.record_request(provider)

            # Store response in conversation and persist
            self._current_conversation.add_message("assistant", response)
            self._persistence.save(self._current_conversation)

            # Update handoff context for next provider
            self._handoff_context = self._package_handoff(system, windowed_messages, response)
            return response
        except Exception as e:
            # Record failure for provider downtime tracking
            self._tracker.record_request(provider)
            self._health_checker.mark_checked(provider.name, False)
            raise

    def _package_handoff(self, system: str, messages: list[dict], response: str) -> str:
        """Package context for handoff to next provider.

        Includes: system prompt, recent conversation history, last response.
        """
        recent_messages = messages[-5:] if len(messages) > 5 else messages
        handoff = {
            "system_prompt": system,
            "recent_context": recent_messages,
            "last_response": response[-2000:] if len(response) > 2000 else response,
            "handoff_timestamp": time.time(),
        }
        return json.dumps(handoff, indent=2)

    def is_available(self) -> bool:
        return len(self._get_available_providers()) > 0


__all__ = [
    "UsageTracker",
    "CyclingBackend",
]