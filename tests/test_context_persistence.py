"""Tests for conversation persistence, context windowing, and provider cycling."""

import tempfile
import time
from pathlib import Path

import pytest

from ai.context_manager import (
    Conversation,
    ConversationPersistence,
    ContextWindowing,
    Message,
    ProviderHealthChecker,
)
from ai.providers import get_providers_sorted, count_providers, AuthMode, ProviderEntry


def test_message_creation():
    """Test basic message creation."""
    msg = Message(role="user", content="Hello!")
    assert msg.role == "user"
    assert msg.content == "Hello!"
    assert msg.timestamp > 0


def test_message_serialization():
    """Test message to/from dict."""
    msg = Message(role="assistant", content="Hi there!")
    msg_dict = msg.to_dict()
    assert msg_dict["role"] == "assistant"
    assert msg_dict["content"] == "Hi there!"

    msg2 = Message.from_dict(msg_dict)
    assert msg2.role == msg.role
    assert msg2.content == msg.content


def test_conversation_creation():
    """Test conversation creation."""
    conv = Conversation(id="test-1")
    assert conv.id == "test-1"
    assert len(conv.messages) == 0
    assert conv.created_at > 0


def test_conversation_add_message():
    """Test adding messages to conversation."""
    conv = Conversation(id="test-2")
    conv.add_message("user", "What is 2+2?")
    conv.add_message("assistant", "2+2 = 4")

    assert len(conv.messages) == 2
    assert conv.messages[0].role == "user"
    assert conv.messages[1].role == "assistant"


def test_conversation_serialization():
    """Test conversation to/from dict."""
    conv = Conversation(id="test-3")
    conv.add_message("user", "Hello")
    conv.add_message("assistant", "Hi!")
    conv.project_id = "proj-123"

    conv_dict = conv.to_dict()
    assert conv_dict["id"] == "test-3"
    assert len(conv_dict["messages"]) == 2
    assert conv_dict["project_id"] == "proj-123"

    conv2 = Conversation.from_dict(conv_dict)
    assert conv2.id == conv.id
    assert len(conv2.messages) == 2


def test_conversation_persistence_save_load():
    """Test saving and loading conversations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ConversationPersistence(Path(tmpdir))

        # Create and save conversation
        conv = Conversation(id="persist-test")
        conv.add_message("user", "Test message")
        storage.save(conv)

        # Load it back
        loaded = storage.load("persist-test")
        assert loaded is not None
        assert loaded.id == "persist-test"
        assert len(loaded.messages) == 1
        assert loaded.messages[0].content == "Test message"


def test_conversation_persistence_list():
    """Test listing conversations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ConversationPersistence(Path(tmpdir))

        # Create multiple conversations
        for i in range(3):
            conv = Conversation(id=f"conv-{i}")
            conv.add_message("user", f"Message {i}")
            storage.save(conv)

        # List all
        conversations = storage.list_conversations()
        assert len(conversations) == 3


def test_conversation_persistence_delete():
    """Test deleting conversations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = ConversationPersistence(Path(tmpdir))

        conv = Conversation(id="delete-me")
        storage.save(conv)
        assert storage.load("delete-me") is not None

        storage.delete("delete-me")
        assert storage.load("delete-me") is None


def test_context_windowing_token_estimation():
    """Test token estimation."""
    windowing = ContextWindowing()

    # Estimate tokens
    text = "This is a test" * 100  # ~1400 chars
    tokens = windowing.estimate_tokens(text)
    assert tokens > 0


def test_context_windowing_conversation_tokens():
    """Test conversation token counting."""
    windowing = ContextWindowing()

    conv = Conversation(id="tokens")
    conv.add_message("user", "Hello" * 100)
    conv.add_message("assistant", "Hi" * 100)

    tokens = windowing.estimate_conversation_tokens(conv.messages)
    assert tokens > 0


def test_context_windowing_fits_provider():
    """Test windowing when conversation fits provider limit."""
    windowing = ContextWindowing()

    conv = Conversation(id="fits")
    conv.add_message("user", "Short message")
    conv.add_message("assistant", "Short response")

    # Should fit in any provider - use ollama (no key needed)
    windowed = windowing.window_for_provider(conv, "ollama")
    assert len(windowed) >= 2  # At least user and assistant message


def test_context_windowing_truncates_long_conversation():
    """Test windowing truncates very long conversations."""
    windowing = ContextWindowing({"ollama": 100})  # Very small limit

    conv = Conversation(id="long")
    for i in range(20):
        conv.add_message("user", "Long message " * 100)
        conv.add_message("assistant", "Long response " * 100)

    # Should be truncated
    windowed = windowing.window_for_provider(conv, "ollama")
    # Should keep some messages but not all 40
    assert len(windowed) < 40


def test_context_windowing_summary_creation():
    """Test creating summary of old messages."""
    windowing = ContextWindowing()

    conv = Conversation(id="summary")
    for i in range(10):
        conv.add_message("user", f"Question {i}")
        conv.add_message("assistant", f"Answer {i}")

    # Get summary of old messages
    summary = windowing._create_summary(conv.messages[:5])
    assert len(summary) > 0
    assert "User asked" in summary or "Answer" in summary


def test_provider_health_checker_should_check():
    """Test health checker timing."""
    checker = ProviderHealthChecker()

    # Should check on first call
    assert checker.should_check("Provider1")

    # Mark checked
    checker.mark_checked("Provider1", True)
    assert not checker.should_check("Provider1")

    # After interval, should check again
    checker.check_interval = 0
    assert checker.should_check("Provider1")


def test_provider_health_checker_status():
    """Test tracking health status."""
    checker = ProviderHealthChecker()

    # Initially unknown
    assert checker.is_healthy("Provider1") is None

    # Mark as healthy
    checker.mark_checked("Provider1", True)
    assert checker.is_healthy("Provider1") is True

    # Mark as unhealthy
    checker.mark_checked("Provider1", False)
    assert checker.is_healthy("Provider1") is False


def test_provider_health_checker_uptime():
    """Test uptime calculation."""
    checker = ProviderHealthChecker()

    # Unknown provider has 100% uptime estimate
    assert checker.get_uptime_percent("Unknown") == 100.0

    # Healthy provider has 100%
    checker.mark_checked("Healthy", True)
    assert checker.get_uptime_percent("Healthy") == 100.0

    # Unhealthy provider has 0%
    checker.mark_checked("Unhealthy", False)
    assert checker.get_uptime_percent("Unhealthy") == 0.0


def test_provider_count():
    """Test provider count with new 8-provider model."""
    counts = count_providers()
    assert counts["total"] == 8
    assert counts["none"] == 1
    assert counts["api_key"] == 5
    assert counts["token"] == 2


def test_provider_sorting():
    """Test providers are sorted by priority."""
    providers = get_providers_sorted()
    for i in range(len(providers) - 1):
        assert providers[i].priority <= providers[i + 1].priority
    # First should be ollama
    assert providers[0].id == "ollama"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
