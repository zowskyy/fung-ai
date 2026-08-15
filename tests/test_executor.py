"""Tests for the executor (generate → detect → run → validate)."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai.executor import detect_language, execute_prompt, _extract_code


class TestDetectLanguage:
    def test_detects_python(self):
        code = 'import os\nprint("hello")'
        assert detect_language(code) == "python"

    def test_detects_javascript(self):
        code = 'console.log("hello")'
        assert detect_language(code) == "javascript"

    def test_detects_rust(self):
        code = 'fn main() { println!("hello"); }'
        assert detect_language(code) == "rust"

    def test_detects_cpp(self):
        code = '#include <iostream>\nint main() { std::cout << "hi"; }'
        assert detect_language(code) == "cpp"

    def test_detects_java(self):
        code = 'public class Main { public static void main(String[] args) {} }'
        assert detect_language(code) == "java"

    def test_defaults_to_python(self):
        code = "hello world"
        assert detect_language(code) == "python"

    def test_detects_python_def(self):
        code = "def main():\n    pass"
        assert detect_language(code) == "python"

    def test_detects_kotlin(self):
        code = "fun main() { println(\"hello\") }"
        assert detect_language(code) == "kotlin"


class TestExtractCode:
    def test_strips_python_fences(self):
        text = '```python\nprint("hello")\n```'
        assert _extract_code(text) == 'print("hello")'

    def test_strips_generic_fences(self):
        text = '```\nprint("hello")\n```'
        assert _extract_code(text) == 'print("hello")'

    def test_strips_comment_header(self):
        text = '# This is a game\n# By AI\nprint("hello")'
        result = _extract_code(text)
        assert result.startswith("print(")

    def test_passes_raw_code(self):
        code = 'print("hello")\nif True:\n    print("world")'
        assert _extract_code(code) == code

    def test_strips_surrounding_whitespace(self):
        text = '  \n  print("hello")  \n  '
        assert _extract_code(text) == 'print("hello")'


class TestExecutePrompt:
    def test_cloud_provider_succeeds(self):
        mock_backend = MagicMock()
        mock_backend.complete.return_value = 'print("hello world")'
        mock_backend.is_available.return_value = True

        with patch("ai.executor._generate_code", return_value=('print("hello world")', "cloud")):
            result = execute_prompt("make a hello world program")

        assert result["success"] is True
        assert "hello world" in result["output"]
        assert result["language"] == "python"
        assert result["provider"] == "cloud"

    def test_empty_response_returns_failure(self):
        with patch("ai.executor._generate_code", return_value=("", "cloud")):
            result = execute_prompt("something")

        assert result["success"] is False
        assert "empty" in result["error"].lower()

    def test_run_failure_returns_failure(self):
        code = 'raise ValueError("intentional error")'
        with patch("ai.executor._generate_code", return_value=(code, "cloud")):
            result = execute_prompt("make something that errors")

        assert result["success"] is False
        assert result["language"] == "python"

    def test_no_providers_raises(self):
        with patch("ai.executor._generate_code", side_effect=RuntimeError("No AI providers")):
            with pytest.raises(RuntimeError, match="No AI providers"):
                execute_prompt("hello")


class TestExecutePromptEndToEnd:
    def test_real_python_hello(self):
        """End-to-end: generate a Python hello, run it, validate output."""
        code = textwrap.dedent('''\
            print("Hello from Creator!")
        ''')
        with patch("ai.executor._generate_code", return_value=(code, "mock")):
            result = execute_prompt("print hello")

        assert result["success"] is True
        assert "Hello from Creator!" in result["output"]
        assert result["language"] == "python"

    def test_real_python_fizzbuzz(self):
        """End-to-end: generate FizzBuzz, run it, validate output."""
        code = textwrap.dedent('''\
            for i in range(1, 16):
                if i % 15 == 0:
                    print("FizzBuzz")
                elif i % 3 == 0:
                    print("Fizz")
                elif i % 5 == 0:
                    print("Buzz")
                else:
                    print(i)
        ''')
        with patch("ai.executor._generate_code", return_value=(code, "mock")):
            result = execute_prompt("make fizzbuzz")

        assert result["success"] is True
        assert "FizzBuzz" in result["output"]
        assert "14" in result["output"]
