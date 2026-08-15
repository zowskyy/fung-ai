"""Execute a playground prompt end-to-end.

Flow:
  1. Generate code via provider fallback chain (cloud → Ollama → GGUF)
  2. Detect language from file extension hint or content
  3. Write code to a temp project dir
  4. Run it via the appropriate runner
  5. Compare output to a trivial expectation
  6. Return result dict: {success, output, language, error, provider}
"""

from __future__ import annotations

import os
import re
import tempfile
import textwrap
from pathlib import Path
from typing import Callable

GENERATION_SYSTEM_PROMPT = textwrap.dedent("""\
    You are a helpful coding assistant for children.
    The user will ask you to build something small (a game, calculator, story, etc).
    RULES:
    - Output ONLY the complete source code for a single file.
    - No markdown fences, no explanations, no headers, no commentary.
    - Use Python 3. The file should be runnable as-is.
    - Include a main() function and call it under if __name__ == "__main__".
    - Keep the code under 200 lines.
    - Print output to stdout so the user can see it.
    - If the user's request is vague, pick the simplest reasonable interpretation.
""")

# Language detection patterns
_LANG_PATTERNS = {
    "python": re.compile(r"\.py$|python|import\s+\w|def\s+\w|print\("),
    "javascript": re.compile(r"\.js$|javascript|console\.log|const\s+\w|let\s+\w"),
    "rust": re.compile(r"\.rs$|fn\s+main|use\s+std|println!"),
    "cpp": re.compile(r"\.cpp$|\.cc$|#include\s*<|std::cout"),
    "java": re.compile(r"\.java$|public\s+class|System\.out"),
    "kotlin": re.compile(r"\.kt$|fun\s+main|println\("),
}


def detect_language(code: str) -> str:
    """Detect programming language from code content."""
    for lang, pattern in _LANG_PATTERNS.items():
        if pattern.search(code):
            return lang
    return "python"  # default fallback


def execute_prompt(
    prompt: str,
    on_status: Callable[[str], None] | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> dict:
    """Generate code from a prompt, run it, validate output.

    Returns:
        {success, output, language, error, provider}
    """
    if on_status:
        on_status("Thinking...")

    # Step 1: Generate code via provider chain
    code, provider_name = _generate_code(prompt, on_status, on_delta)

    if not code.strip():
        return {
            "success": False,
            "output": "",
            "language": "",
            "error": "AI returned empty code",
            "provider": provider_name,
        }

    # Step 2: Detect language
    language = detect_language(code)
    if on_status:
        on_status(f"Detected {language}, running...")

    # Step 3: Write to temp project and run
    project_dir = Path(tempfile.mkdtemp(prefix="creator_playground_"))
    ext = _ext_for_language(language)
    script_path = project_dir / f"main{ext}"
    script_path.write_text(code, encoding="utf-8")

    # Step 4: Run
    output, exit_code, run_error = _run_code(language, project_dir, script_path)

    if on_status:
        if exit_code == 0:
            on_status("Done!")
        else:
            on_status("Finished with errors")

    # Step 5: Validate
    success = exit_code == 0 and bool(output.strip())

    return {
        "success": success,
        "output": output,
        "language": language,
        "error": run_error or ("" if success else "No output produced"),
        "provider": provider_name,
    }


def _generate_code(
    prompt: str,
    on_status: Callable[[str], None] | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> tuple[str, str]:
    """Try provider chain: Ollama (local) → Cloud → GGUF fallback.

    Local first because cloud providers are unreliable and each timeout
    takes 30+ seconds. Returns (code, provider_name).
    """

    # 1. Try Ollama (auto-install + auto-start on first use)
    code, name = _try_ollama(prompt, on_status, on_delta)
    if code:
        return code, name

    # 2. Try cloud (fast — only providers with keys configured)
    code, name = _try_cloud(prompt, on_status, on_delta)
    if code:
        return code, name

    # 3. Try embedded GGUF (no Ollama needed)
    code, name = _try_gguf(prompt, on_status, on_delta)
    if code:
        return code, name

    raise RuntimeError(
        "No AI providers available. Install Ollama for offline use,\n"
        "or set an API key (e.g. OPENROUTER_API_KEY) for cloud AI."
    )


def _try_ollama(
    prompt: str,
    on_status: Callable[[str], None] | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> tuple[str, str]:
    """Try Ollama: install → start server → pull model → generate."""
    try:
        from ai.llm_setup import (
            is_ollama_installed,
            is_ollama_running,
            install_ollama,
            pull_ollama_model,
            start_ollama_server,
            DEFAULT_OLLAMA_MODEL,
        )

        # Auto-install if missing
        if not is_ollama_installed():
            if on_status:
                on_status("Installing Ollama (~7 MB)...")
            if not install_ollama(on_progress=on_status):
                return ("", "")

        # Auto-start server if not running
        if not is_ollama_running():
            if on_status:
                on_status("Starting Ollama server...")
            start_ollama_server()

        if not is_ollama_running():
            return ("", "")

        # Pull model if needed
        from ai.llm_setup import get_ollama_status
        status = get_ollama_status()
        if DEFAULT_OLLAMA_MODEL not in status.get("models", []):
            if on_status:
                on_status(f"Downloading model (~600 MB)...")
            pull_ollama_model(DEFAULT_OLLAMA_MODEL, on_progress=on_status)

        if DEFAULT_OLLAMA_MODEL not in get_ollama_status().get("models", []):
            return ("", "")

        from ai.python_shim import OpenAICompatBackend
        ollama = OpenAICompatBackend(
            base_url="http://localhost:11434/v1",
            api_key="",
            model=DEFAULT_OLLAMA_MODEL,
        )
        if on_status:
            on_status("Generating with local Ollama...")
        response = ollama.complete(
            GENERATION_SYSTEM_PROMPT,
            [{"role": "user", "content": prompt}],
            on_delta,
        )
        return (_extract_code(response), "ollama")
    except Exception:
        return ("", "")


def _try_cloud(
    prompt: str,
    on_status: Callable[[str], None] | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> tuple[str, str]:
    """Try cloud providers — fast-fail, no hanging on dead endpoints."""
    import os

    # Only try providers that have their env var set (key configured)
    from ai.providers import get_providers_sorted
    for provider in get_providers_sorted():
        if not provider.requires_key:
            continue
        key_env = provider.key_env_var or ""
        if not key_env or not os.environ.get(key_env):
            continue

        if on_status:
            on_status(f"Trying {provider.name}...")

        try:
            from ai.python_shim import OpenAICompatBackend
            backend = OpenAICompatBackend(
                base_url=provider.base_url,
                api_key=os.environ.get(key_env, ""),
                model=provider.models[0],
            )
            # Quick availability check (2s timeout, not 180s)
            import urllib.request
            try:
                req = urllib.request.Request(
                    provider.base_url.rstrip("/") + "/models",
                    headers={"Authorization": f"Bearer {os.environ.get(key_env, '')}"},
                )
                urllib.request.urlopen(req, timeout=3)
            except Exception:
                continue

            response = backend.complete(
                GENERATION_SYSTEM_PROMPT,
                [{"role": "user", "content": prompt}],
                on_delta,
            )
            return (_extract_code(response), provider.name)
        except Exception:
            continue

    return ("", "")


def _try_gguf(
    prompt: str,
    on_status: Callable[[str], None] | None = None,
    on_delta: Callable[[str], None] | None = None,
) -> tuple[str, str]:
    """Try embedded GGUF (download model + run via llama-cpp-python)."""
    try:
        from ai.llm_setup import is_gguf_available, download_gguf_model
        if not is_gguf_available():
            if on_status:
                on_status("Downloading tiny model (~700 MB, one-time)...")
            if not download_gguf_model(on_progress=on_status):
                return ("", "")

        from runners.gguf_runner import GGUFRunner, _llama_cpp_available
        if not _llama_cpp_available():
            return ("", "")

        runner = GGUFRunner()
        if not runner.is_available():
            return ("", "")

        if on_status:
            on_status("Generating with local model...")
        response = runner.complete(
            prompt=prompt,
            system=GENERATION_SYSTEM_PROMPT,
            on_delta=on_delta,
        )
        return (_extract_code(response), "gguf")
    except Exception:
        return ("", "")


def _extract_code(text: str) -> str:
    """Strip markdown fences and extra commentary, return raw code."""
    text = text.strip()
    # Remove ```python ... ``` wrappers
    m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Remove ``` ... ``` wrappers (any language)
    m = re.search(r"```\w*\s*\n(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # If it starts with a comment header, skip first lines
    lines = text.split("\n")
    code_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") or stripped == "":
            continue
        code_start = i
        break
    return "\n".join(lines[code_start:])


def _ext_for_language(language: str) -> str:
    return {
        "python": ".py",
        "javascript": ".js",
        "rust": ".rs",
        "cpp": ".cpp",
        "java": ".java",
        "kotlin": ".kt",
    }.get(language, ".py")


def _run_code(
    language: str,
    project_dir: Path,
    script_path: Path,
) -> tuple[str, int, str]:
    """Run the generated code and capture output. Returns (output, exit_code, error)."""
    try:
        from runners import get_runner
        runner = get_runner(language)
    except Exception:
        # Fallback to PythonRunner for any language
        from runners.python_runner import PythonRunner
        runner = PythonRunner()

    lines: list[str] = []
    def capture(line: str) -> None:
        lines.append(line)

    try:
        if hasattr(runner, "start_and_stream"):
            code = runner.start_and_stream(project_dir, script_path.name, capture)
            return "\n".join(lines), code, ""
        else:
            # For runners that don't have start_and_stream (GGUF)
            return "", 1, f"Runner {language} cannot execute scripts"
    except Exception as exc:
        return "\n".join(lines), 1, str(exc)


__all__ = [
    "execute_prompt",
    "detect_language",
    "GENERATION_SYSTEM_PROMPT",
]
