"""Conversation context management: persistence, windowing, and summarization.

This module handles:
- Persistent storage of conversations (survives app restart)
- Smart context windowing (summarize old messages for long conversations)
- Token counting per provider (know limits before hitting them)
- Graceful context truncation when response too long
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime

# Conversation storage location: ~/.creator/conversations/
CONVERSATIONS_DIR = Path.home() / ".creator" / "conversations"


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> Message:
        return Message(**data)


@dataclass
class Conversation:
    """A complete conversation thread."""
    id: str
    messages: list[Message] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    project_id: str = ""
    metadata: dict = field(default_factory=dict)

    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append(Message(role=role, content=content))
        self.last_updated = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "last_updated": self.last_updated,
            "project_id": self.project_id,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict) -> Conversation:
        conv = Conversation(
            id=data["id"],
            created_at=data.get("created_at", time.time()),
            last_updated=data.get("last_updated", time.time()),
            project_id=data.get("project_id", ""),
            metadata=data.get("metadata", {}),
        )
        conv.messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return conv


class ConversationPersistence:
    """Persistent storage for conversations."""

    def __init__(self, storage_dir: Path | None = None):
        self.storage_dir = storage_dir or CONVERSATIONS_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_conversation_path(self, conversation_id: str) -> Path:
        """Get file path for a conversation."""
        return self.storage_dir / f"{conversation_id}.json"

    def save(self, conversation: Conversation) -> None:
        """Save conversation to disk."""
        path = self._get_conversation_path(conversation.id)
        path.write_text(json.dumps(conversation.to_dict(), indent=2), encoding="utf-8")

    def load(self, conversation_id: str) -> Conversation | None:
        """Load conversation from disk."""
        path = self._get_conversation_path(conversation_id)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Conversation.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return None

    def list_conversations(self) -> list[Conversation]:
        """List all saved conversations."""
        conversations = []
        for path in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                conversations.append(Conversation.from_dict(data))
            except (json.JSONDecodeError, OSError):
                continue
        return sorted(conversations, key=lambda c: c.last_updated, reverse=True)

    def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        path = self._get_conversation_path(conversation_id)
        if path.exists():
            path.unlink()
            return True
        return False


class ContextWindowing:
    """Smart context windowing for long conversations.

    Keeps recent messages in full, summarizes older parts to stay under token limits.
    """

    def __init__(self, max_tokens_per_provider: dict[str, int] | None = None):
        # Default token limits per provider (conservative estimates)
        default_limits = {
            "BlockRun": 4000,          # GPT-4o-mini context
            "Groq": 8000,              # Llama 3.1 70B
            "Cerebras": 200000,        # Llama 3.1 very high
            "Mistral": 32000,          # Mistral large
            "Anthropic": 200000,       # Claude 3.5 Sonnet
            "default": 4000,
        }
        if max_tokens_per_provider:
            # Merge custom limits with defaults, ensuring "default" is always present
            self.token_limits = {**default_limits, **max_tokens_per_provider}
            if "default" not in self.token_limits:
                self.token_limits["default"] = 4000
        else:
            self.token_limits = default_limits

    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation: 1 token ≈ 4 chars."""
        return max(1, len(text) // 4)

    def estimate_conversation_tokens(self, messages: list[Message]) -> int:
        """Estimate total tokens in conversation."""
        total = 0
        for msg in messages:
            total += self.estimate_tokens(msg.content) + 50  # 50 tokens for overhead per message
        return total

    def window_for_provider(self, conversation: Conversation, provider_name: str) -> list[dict]:
        """Window conversation to fit provider's context limit.

        Strategy:
        1. Keep all recent messages (last 5 user messages minimum)
        2. If still over limit, summarize older messages
        3. Return list of dicts compatible with API (role, content)
        """
        limit = self.token_limits.get(provider_name, self.token_limits["default"])

        # Convert messages to API format
        api_messages = [{"role": m.role, "content": m.content} for m in conversation.messages]

        # Calculate tokens
        total_tokens = self.estimate_conversation_tokens(conversation.messages)

        if total_tokens <= limit * 0.8:  # 80% threshold
            return api_messages

        # Need to window: keep recent messages, remove/summarize older ones
        # Keep at least last 5 user messages
        recent_threshold = min(10, len(conversation.messages))
        recent_messages = conversation.messages[-recent_threshold:]

        # Check if recent messages alone fit
        recent_tokens = self.estimate_conversation_tokens(recent_messages)
        if recent_tokens <= limit * 0.9:  # 90% of limit for safety
            summary = self._create_summary(conversation.messages[:-recent_threshold])
            if summary:
                result = [{"role": "system", "content": f"[SUMMARY OF EARLIER CONTEXT]\n{summary}"}]
                result.extend([{"role": m.role, "content": m.content} for m in recent_messages])
                return result
            return [{"role": m.role, "content": m.content} for m in recent_messages]

        # Recent messages alone are too long - aggressive windowing
        return [{"role": m.role, "content": m.content} for m in recent_messages[-5:]]

    def _create_summary(self, messages: list[Message]) -> str:
        """Create a brief summary of conversation context."""
        if not messages:
            return ""

        # Extract key points from messages
        user_queries = [m.content for m in messages if m.role == "user"][-3:]
        assistant_responses = [m.content[:200] for m in messages if m.role == "assistant"][-3:]

        summary_parts = []
        if user_queries:
            summary_parts.append(f"User asked: {'; '.join(user_queries[:2])}")
        if assistant_responses:
            summary_parts.append(f"Previous responses touched on: {'; '.join(assistant_responses[:2])}")

        return " | ".join(summary_parts) if summary_parts else "Earlier context in conversation"


class ProviderHealthChecker:
    """Periodic health checks for providers."""

    def __init__(self):
        self.last_checks: dict[str, float] = {}
        self.last_status: dict[str, bool] = {}  # True = healthy
        self.check_interval = 300  # 5 minutes

    def should_check(self, provider_name: str) -> bool:
        """Check if it's time to ping this provider."""
        last_check = self.last_checks.get(provider_name, 0)
        return (time.time() - last_check) > self.check_interval

    def mark_checked(self, provider_name: str, is_healthy: bool) -> None:
        """Record a health check result."""
        self.last_checks[provider_name] = time.time()
        self.last_status[provider_name] = is_healthy

    def is_healthy(self, provider_name: str) -> bool | None:
        """Get last known health status (None = never checked)."""
        return self.last_status.get(provider_name)

    def get_uptime_percent(self, provider_name: str) -> float:
        """Estimate uptime based on successful checks."""
        # This would be expanded with persistent tracking
        return 100.0 if self.is_healthy(provider_name) is not False else 0.0


__all__ = [
    "Message",
    "Conversation",
    "ConversationPersistence",
    "ContextWindowing",
    "ProviderHealthChecker",
    "CONVERSATIONS_DIR",
]
