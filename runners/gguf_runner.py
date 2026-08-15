"""Run a GGUF model locally via llama-cpp-python subprocess.

This is the "no Ollama, no server" fallback — a single Python process that
loads the GGUF file and runs inference directly. Requires llama-cpp-python
to be installed (pip install llama-cpp-python).

The model file is managed by ai/llm_setup.py (downloaded from HuggingFace on demand).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable

from ai.llm_setup import GGUF_FILE, is_gguf_available


class GGUFRunner:
    """Runs inference on a GGUF model using llama-cpp-python subprocess."""

    name = "Embedded GGUF"

    def __init__(self, model_path: Path | None = None, n_ctx: int = 2048):
        self.model_path = model_path or GGUF_FILE
        self.n_ctx = n_ctx
        self._process: subprocess.Popen | None = None

    def is_available(self) -> bool:
        if not self.model_path.exists():
            return False
        return _llama_cpp_available()

    def complete(
        self,
        prompt: str,
        system: str = "",
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        """Run inference and return the full response text."""
        if not self.is_available():
            raise RuntimeError("GGUF model or llama-cpp-python not available")

        script = _build_inference_script(
            model_path=str(self.model_path),
            prompt=prompt,
            system=system,
            n_ctx=self.n_ctx,
        )
        kwargs: dict = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        if sys.platform == "win32":
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        self._process = subprocess.Popen(
            [sys.executable, "-c", script],
            **kwargs,
        )
        chunks: list[str] = []
        if self._process.stdout:
            for line in self._process.stdout:
                line = line.rstrip("\r\n")
                if line:
                    chunks.append(line)
                    if on_delta:
                        on_delta(line + "\n")
        self._process.wait()
        return "\n".join(chunks)

    def stop(self) -> None:
        proc = self._process
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()


def _llama_cpp_available() -> bool:
    """Check if llama-cpp-python is importable."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import llama_cpp; print('ok')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and "ok" in result.stdout
    except Exception:
        return False


def _build_inference_script(
    model_path: str,
    prompt: str,
    system: str = "",
    n_ctx: int = 2048,
) -> str:
    """Build a Python script string that runs llama-cpp-python inference.

    We write it as a string and execute via subprocess to avoid import
    issues in the main process.
    """
    system_escaped = system.replace("\\", "\\\\").replace('"', '\\"')
    prompt_escaped = prompt.replace("\\", "\\\\").replace('"', '\\"')
    return (
        'from llama_cpp import Llama\n'
        f'llm = Llama(model_path=r"{model_path}", n_ctx={n_ctx}, verbose=False)\n'
        f'messages = [{{"role": "system", "content": "{system_escaped}"}}, '
        f'{{"role": "user", "content": "{prompt_escaped}"}}]\n'
        'output = llm.create_chat_completion(messages=messages, max_tokens=1500)\n'
        'print(output["choices"][0]["message"]["content"])\n'
    )


__all__ = ["GGUFRunner"]
