from __future__ import annotations

from runners.detector import detect_all, detect_python


def test_python_always_available():
    tool = detect_python()
    assert tool.available
    assert tool.path


def test_detect_all_returns_expected_names():
    names = {tool.name for tool in detect_all()}
    assert {"Python", "Java", "Rust", "C++", "JavaScript", "Kotlin"} == names
