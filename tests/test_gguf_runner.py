"""Tests for the GGUF runner (embedded llama-cpp-python)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runners.gguf_runner import GGUFRunner, _llama_cpp_available


class TestLLamaCppAvailable:
    def test_available_when_importable(self):
        with patch("runners.gguf_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="ok\n")
            assert _llama_cpp_available() is True

    def test_not_available_when_import_fails(self):
        with patch("runners.gguf_runner.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")
            assert _llama_cpp_available() is False

    def test_not_available_on_timeout(self):
        with patch("runners.gguf_runner.subprocess.run", side_effect=TimeoutError):
            assert _llama_cpp_available() is False


class TestGGUFRunner:
    def test_is_available_false_when_no_model(self):
        with patch("runners.gguf_runner.GGUF_FILE") as mock_file, \
             patch("runners.gguf_runner._llama_cpp_available", return_value=True):
            mock_file.exists.return_value = False
            runner = GGUFRunner()
            assert runner.is_available() is False

    def test_is_available_false_when_no_llama_cpp(self):
        with patch("runners.gguf_runner.GGUF_FILE") as mock_file, \
             patch("runners.gguf_runner._llama_cpp_available", return_value=False):
            mock_file.exists.return_value = True
            runner = GGUFRunner()
            assert runner.is_available() is False

    def test_is_available_true_when_all_present(self):
        with patch("runners.gguf_runner.GGUF_FILE") as mock_file, \
             patch("runners.gguf_runner._llama_cpp_available", return_value=True):
            mock_file.exists.return_value = True
            runner = GGUFRunner()
            assert runner.is_available() is True

    def test_complete_raises_when_not_available(self):
        with patch("runners.gguf_runner.GGUF_FILE") as mock_file, \
             patch("runners.gguf_runner._llama_cpp_available", return_value=False):
            mock_file.exists.return_value = True
            runner = GGUFRunner()
            with pytest.raises(RuntimeError, match="not available"):
                runner.complete("hello")

    def test_stop_kills_process(self):
        runner = GGUFRunner()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        runner._process = mock_proc
        runner.stop()
        mock_proc.terminate.assert_called_once()

    def test_stop_does_nothing_when_no_process(self):
        runner = GGUFRunner()
        runner._process = None
        runner.stop()  # should not raise

    def test_stop_does_nothing_when_already_exited(self):
        runner = GGUFRunner()
        mock_proc = MagicMock()
        mock_proc.poll.return_value = 0
        runner._process = mock_proc
        runner.stop()
        mock_proc.terminate.assert_not_called()
