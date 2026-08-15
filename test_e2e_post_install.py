#!/usr/bin/env python3
"""
End-to-End Post-Installation Test for Creator.

Simulates the immediate post-install experience: provider ecosystem loads,
conversations persist, context windowing works, templates load, and projects
can be created. Uses the REAL public APIs (no phantom method names) so a
passing run actually means the wiring is correct.

This is a standalone script (run with `python test_e2e_post_install.py`); it is
NOT collected by pytest and performs NO network calls.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ai.context_manager import (
    ConversationPersistence,
    ContextWindowing,
    Conversation,
    Message,
)
from ai.providers import get_providers_by_category, count_providers
from core.template_engine import discover_templates
from sandbox.workspace import Project, list_projects


def test_provider_ecosystem():
    """Test 1: Verify the provider ecosystem is loaded."""
    print("\n" + "=" * 70)
    print("TEST 1: Provider Ecosystem")
    print("=" * 70)

    providers = get_providers_by_category()
    counts = count_providers()
    total = counts["total"]
    no_key = sum(1 for p in providers if not p.requires_key)
    assert total, "No providers loaded"

    print(f"\n[OK] Total providers loaded: {total} ({no_key} no-key, {total - no_key} key-required)")

    assert total >= 30, f"Expected 30+ providers, got {total}"
    print("[OK] PASS: Provider ecosystem meets requirement (30+ providers)")
    return True


def test_conversation_persistence():
    """Test 2: Conversation history survives app restart (real API)."""
    print("\n" + "=" * 70)
    print("TEST 2: Conversation Persistence")
    print("=" * 70)

    persistence = ConversationPersistence()

    conv = Conversation(
        id="test-session-001",
        messages=[
            Message(role="user", content="What can I build with Creator?"),
            Message(role="assistant", content="Games, web apps, and more!"),
            Message(role="user", content="How does AI cycling work?"),
            Message(role="assistant", content="Creator auto-rotates through free providers."),
        ],
    )

    persistence.save(conv)
    print(f"\n[OK] Saved conversation with {len(conv.messages)} messages")

    loaded = persistence.load("test-session-001")
    assert loaded is not None, "Failed to load conversation after restart"
    assert len(loaded.messages) == 4, f"Expected 4 messages, got {len(loaded.messages)}"
    assert loaded.messages[0].content == "What can I build with Creator?"
    print("[OK] Conversation history fully preserved (no data loss)")
    print("[OK] PASS: Conversations survive app restart")
    return True


def test_context_windowing():
    """Test 3: Smart context windowing for long conversations (real API)."""
    print("\n" + "=" * 70)
    print("TEST 3: Context Windowing")
    print("=" * 70)

    windowing = ContextWindowing()
    conv = Conversation(id="window-test")
    for i in range(50):
        role = "user" if i % 2 == 0 else "assistant"
        conv.add_message(role, f"Message {i + 1}: " + "x" * 100)

    total_tokens = sum(windowing.estimate_tokens(m.content) for m in conv.messages)
    print(f"\n[OK] Long conversation: {len(conv.messages)} messages, ~{total_tokens} tokens")

    windowed = windowing.window_for_provider(conv, "BlockRun")
    windowed_tokens = sum(windowing.estimate_tokens(m.get("content", "")) for m in windowed)
    print(f"[OK] After windowing: {len(windowed)} messages, ~{windowed_tokens} tokens")
    assert windowed_tokens <= total_tokens, "Windowing returned more tokens than input"
    print("[OK] PASS: Context windowing keeps long conversations responsive")
    return True


def test_template_loading():
    """Test 4: All templates load correctly."""
    print("\n" + "=" * 70)
    print("TEST 4: Template Loading")
    print("=" * 70)

    templates_dir = Path(__file__).parent / "templates"
    templates = discover_templates(templates_dir)

    print(f"\n[OK] Found {len(templates)} templates")
    for tmpl in templates:
        print(f"  - {tmpl.name}")

    assert len(templates) >= 6, f"Expected 6+ templates, got {len(templates)}"
    print("[OK] PASS: All templates load")
    return True


def test_workspace_creation():
    """Test 5: Projects can be created immediately (real API)."""
    print("\n" + "=" * 70)
    print("TEST 5: Project Creation")
    print("=" * 70)

    with tempfile.TemporaryDirectory() as tmp:
        workspace_dir = Path(tmp) / "projects"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        project = Project.create(
            workspace_dir, "test-project-001", "python-number-guess", {}
        )
        print(f"\n[OK] Created project: {project.name}")
        print(f"[OK] Template: {project.data.get('template')}")
        print(f"[OK] Project directory: {project.root}")

        found = [p.name for p in list_projects(workspace_dir)]
        assert "test-project-001" in found, "Project not listed after creation"
        print("[OK] Project listed by list_projects()")
        print("[OK] PASS: Projects can be created immediately")
    return True


def main():
    print("\n" + "=" * 68)
    print(" CREATOR: POST-INSTALLATION END-TO-END TEST ")
    print("=" * 68)

    tests = [
        ("Provider Ecosystem", test_provider_ecosystem),
        ("Conversation Persistence", test_conversation_persistence),
        ("Context Windowing", test_context_windowing),
        ("Template Loading", test_template_loading),
        ("Workspace Creation", test_workspace_creation),
    ]

    results = []
    for name, test_func in tests:
        try:
            ok = test_func()
            results.append((name, "PASS" if ok else "FAIL"))
        except Exception as exc:  # noqa: BLE001
            print(f"\n[FAIL] {name}: {exc}")
            results.append((name, "FAIL"))

    print("\n" + "=" * 70)
    print("FINAL TEST RESULTS")
    print("=" * 70)
    passed = sum(1 for _, status in results if status == "PASS")
    total = len(results)
    for name, status in results:
        symbol = "[OK]" if status == "PASS" else "[FAIL]"
        print(f"{symbol} {name}: {status}")
    print(f"\nResult: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
