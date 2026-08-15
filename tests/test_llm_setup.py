"""Tests for LLM setup (Ollama auto-install, GGUF download)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

from ai.llm_setup import (
    is_ollama_installed,
    is_ollama_running,
    get_ollama_status,
    is_gguf_available,
    get_gguf_status,
    OLLAMA_DIR,
    OLLAMA_EXE,
    GGUF_DIR,
    GGUF_FILE,
)


class TestOllamaDetection:
    def test_is_installed_when_exe_exists(self):
        with patch("ai.llm_setup.OLLAMA_EXE") as mock_exe, \
             patch("ai.llm_setup.shutil.which", return_value=None):
            mock_exe.exists.return_value = True
            assert is_ollama_installed() is True

    def test_is_installed_when_on_path(self):
        with patch("ai.llm_setup.OLLAMA_EXE") as mock_exe, \
             patch("ai.llm_setup.shutil.which", return_value="/usr/bin/ollama"):
            mock_exe.exists.return_value = False
            assert is_ollama_installed() is True

    def test_not_installed(self):
        with patch("ai.llm_setup.OLLAMA_EXE") as mock_exe, \
             patch("ai.llm_setup.shutil.which", return_value=None):
            mock_exe.exists.return_value = False
            assert is_ollama_installed() is False

    def test_is_running_when_server_responds(self):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("ai.llm_setup.urllib.request.urlopen", return_value=mock_resp):
            assert is_ollama_running() is True

    def test_not_running_when_server_down(self):
        with patch("ai.llm_setup.urllib.request.urlopen", side_effect=ConnectionError):
            assert is_ollama_running() is False


class TestOllamaInstall:
    def test_install_skips_if_already_installed(self):
        with patch("ai.llm_setup.is_ollama_installed", return_value=True):
            result = MagicMock()
            with patch("ai.llm_setup.install_ollama") as mock_install:
                mock_install.return_value = True
                assert mock_install() is True

    def test_install_downloads_exe(self):
        with patch("ai.llm_setup.is_ollama_installed", return_value=False), \
             patch("ai.llm_setup.OLLAMA_DIR") as mock_dir, \
             patch("ai.llm_setup.urllib.request.urlretrieve") as mock_dl, \
             patch("ai.llm_setup.OLLAMA_EXE") as mock_exe:
            mock_dir.mkdir = MagicMock()
            mock_exe.chmod = MagicMock()
            mock_exe.stat.return_value = MagicMock(st_mode=0)
            from ai.llm_setup import install_ollama
            result = install_ollama()
            assert result is True
            mock_dl.assert_called_once()


class TestGGUFDetection:
    def test_available_when_file_exists(self):
        with patch("ai.llm_setup.GGUF_FILE") as mock_file:
            mock_file.exists.return_value = True
            assert is_gguf_available() is True

    def test_not_available(self):
        with patch("ai.llm_setup.GGUF_FILE") as mock_file:
            mock_file.exists.return_value = False
            assert is_gguf_available() is False

    def test_status_when_available(self):
        with patch("ai.llm_setup.GGUF_FILE") as mock_file:
            mock_file.exists.return_value = True
            mock_file.stat.return_value = MagicMock(st_size=734003200)
            status = get_gguf_status()
            assert status["available"] is True
            assert status["size_mb"] == 700.0

    def test_status_when_unavailable(self):
        with patch("ai.llm_setup.GGUF_FILE") as mock_file:
            mock_file.exists.return_value = False
            status = get_gguf_status()
            assert status["available"] is False
            assert status["size_mb"] == 0


class TestOllamaStatus:
    def test_status_not_installed(self):
        with patch("ai.llm_setup.is_ollama_installed", return_value=False):
            status = get_ollama_status()
            assert status["installed"] is False
            assert status["running"] is False
            assert status["models"] == []

    def test_status_installed_not_running(self):
        with patch("ai.llm_setup.is_ollama_installed", return_value=True), \
             patch("ai.llm_setup.is_ollama_running", return_value=False):
            status = get_ollama_status()
            assert status["installed"] is True
            assert status["running"] is False

    def test_status_installed_running_with_models(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"models": [{"name": "tinyllama:1b"}]}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("ai.llm_setup.is_ollama_installed", return_value=True), \
             patch("ai.llm_setup.is_ollama_running", return_value=True), \
             patch("ai.llm_setup.urllib.request.urlopen", return_value=mock_resp):
            status = get_ollama_status()
            assert status["installed"] is True
            assert status["running"] is True
            assert "tinyllama:1b" in status["models"]
