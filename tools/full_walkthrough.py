"""Full user experience walkthrough — find every broken thing."""
import os, sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
app = QApplication(sys.argv)

from app.main_window import MainWindow
w = MainWindow()

print("=== STARTUP ===")
print(f"Stack count: {w.stack.count()}")
print(f"Default screen: {type(w.stack.currentWidget()).__name__}")

# --- HOME ---
print("\n=== HOME SCREEN ===")
w.show_home()
print(f"Home visible: {w.stack.currentWidget() is w.home}")
tools = w.home.tools_row
print(f"Tools row count: {tools.count()}")

# --- PLAYGROUND ---
print("\n=== PLAYGROUND SCREEN ===")
w.show_playground()
pg = w.playground
print(f"Playground visible: {w.stack.currentWidget() is pg}")
print(f"Prompt field: {pg.prompt_field is not None}")
print(f"Go button: {pg.go_btn is not None}")
print(f"Go button text: '{pg.go_btn.text()}'")
print(f"Output area: {pg.output_area is not None}")
print(f"Status label: {pg.status_label is not None}")
print(f"Try again btn hidden: {pg.try_again_btn.isHidden()}")
print(f"Open editor btn hidden: {pg.open_editor_btn.isHidden()}")

# --- WIZARD ---
print("\n=== WIZARD ===")
w.show_wizard()
print(f"Wizard visible: {w.stack.currentWidget() is w.wizard}")
templates = w.wizard.templates
print(f"Template count: {len(templates)}")
for t in templates[:3]:
    print(f"  {t.manifest.get('id', '?')}: {t.manifest.get('name', '?')}")

# --- EDITOR ---
print("\n=== EDITOR ===")
print(f"Editor exists: {w.editor is not None}")
print(f"Editor chat_log: {hasattr(w.editor, 'chat_log')}")
print(f"Editor _backend: {hasattr(w.editor, '_backend')}")

# --- SETTINGS ---
print("\n=== SETTINGS ===")
from ai import settings
print(f"Auth file: {settings.AUTH_FILE}")
print(f"Cycle index: {settings.get_cycle_index()}")

# --- PROVIDERS ---
print("\n=== PROVIDERS ===")
from ai.providers import count_providers, get_providers_sorted
counts = count_providers()
print(f"Total: {counts['total']}, No-key: {counts['no_key']}, Requires-key: {counts['requires_key']}")

import os as _os
providers_with_env = []
for p in get_providers_sorted():
    if p.requires_key and p.key_env_var and _os.environ.get(p.key_env_var):
        providers_with_env.append(p.name)
print(f"Providers with env key set: {providers_with_env}")

# --- OLLAMA ---
print("\n=== OLLAMA ===")
from ai.llm_setup import is_ollama_installed, is_ollama_running
print(f"Installed: {is_ollama_installed()}")
print(f"Running: {is_ollama_running()}")

# --- GGUF ---
print("\n=== GGUF ===")
from ai.llm_setup import is_gguf_available, get_gguf_status
print(f"Available: {is_gguf_available()}")
gs = get_gguf_status()
print(f"Status: {gs}")

# --- EXECUTOR ---
print("\n=== EXECUTOR ===")
from ai.executor import execute_prompt, GENERATION_SYSTEM_PROMPT
print(f"execute_prompt: {callable(execute_prompt)}")
print(f"System prompt length: {len(GENERATION_SYSTEM_PROMPT)}")
print(f"System prompt preview: {GENERATION_SYSTEM_PROMPT[:80]}...")

# --- RUNNERS ---
print("\n=== RUNNERS ===")
from runners import get_runner, PythonRunner, NoRunnerForLanguage
for lang in ["python", "javascript", "java", "rust", "cpp", "kotlin"]:
    try:
        r = get_runner(lang)
        print(f"  {lang}: {type(r).__name__}")
    except NoRunnerForLanguage as e:
        print(f"  {lang}: MISSING - {e}")

# --- GGUF RUNNER ---
print("\n=== GGUF RUNNER ===")
from runners.gguf_runner import GGUFRunner, _llama_cpp_available
print(f"llama-cpp-python available: {_llama_cpp_available()}")
runner = GGUFRunner()
print(f"GGUFRunner.is_available: {runner.is_available()}")

# --- CYCLING BACKEND ---
print("\n=== CYCLING BACKEND ===")
from ai.cycling import CyclingBackend
cb = CyclingBackend()
print(f"Available providers: {len(cb._get_available_providers())}")
print(f"Total providers loaded: {len(cb._providers)}")

# --- SANDBOX ---
print("\n=== SANDBOX ===")
from sandbox.workspace import Project
print(f"Project class: {Project}")

# --- GIT ---
print("\n=== GIT ===")
from repo.git_manager import RepoManager
print(f"RepoManager: {RepoManager}")

# --- NOTIFICATIONS ---
print("\n=== NOTIFICATIONS ===")
from app.notifications import notify_complete
print(f"notify_complete: {callable(notify_complete)}")

# --- TEMPLATE ENGINE ---
print("\n=== TEMPLATE ENGINE ===")
from core.template_engine import discover_templates
from app.paths import templates_dir
td = templates_dir()
tpls = discover_templates(td)
print(f"Templates dir: {td}")
print(f"Discovered: {len(tpls)}")

# --- NAVIGATION ---
print("\n=== NAVIGATION FLOW ===")
w.show_home()
print(f"After show_home: {type(w.stack.currentWidget()).__name__}")
w.show_playground()
print(f"After show_playground: {type(w.stack.currentWidget()).__name__}")
w.show_wizard()
print(f"After show_wizard: {type(w.stack.currentWidget()).__name__}")

print("\n=== DONE ===")
w.close()
