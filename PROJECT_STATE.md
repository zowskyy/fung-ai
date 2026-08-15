# Project State: Creator — opencode Feature Parity

**Date:** 2026-08-14  
**Directory:** `C:\Users\thewi\Desktop\Creator`  
**Save Point:** `.snapshots/savepoint-20260814-070418` (72 files)  
**Status:** 9/14 frontend features complete, Model Cycling system done

## Available Toolchains
| Language    | Toolchain            | Available? |
|-------------|----------------------|------------|
| Python      | venv (PySide6, pytest) | ✅        |
| Java        | OpenJDK 21.0.12      | ✅        |
| Rust        | cargo 1.97.1         | ✅        |
| C++         | g++ 16.1.0 (MinGW)   | ✅        |
| JavaScript  | Node.js v24.19.0     | ✅        |
| Kotlin      | kotlinc             | ❌ Not installed |

## Roadmap Status

### ✅ Phase 0-6: Language Support (COMPLETE)
All 6 language runners, templates, and stress tests working. 46 tests passing.

### ✅ Feature 1: Sidebar Layout (COMPLETE)
- Created `app/widgets/sidebar.py` — persistent left sidebar
- Modified `app/main_window.py` — sidebar + content area layout
- Modified `app/screens/home.py` — simplified (project list moved to sidebar)
- Project list with active project highlighting
- Toolchain status pills at bottom

### ✅ Feature 2: Multi-Session Tabs (COMPLETE)
- Modified `app/screens/editor.py` — `QTabBar` for multiple open projects
- Tab close support, tab switching with full state preservation
- Duplicate project detection (switches to existing tab)
- Session state isolation per tab

### ✅ Feature 3: Build/Plan Mode Toggle (COMPLETE)
- Added toggle button in editor header (green=Build, blue=Plan)
- Build mode: AI can edit files (full access)
- Plan mode: AI is read-only, suggests improvements without file changes
- System prompt differentiates between modes
- Replaces old checkbox with prominent toggle

### ✅ Feature 4: Markdown Rendering in Chat (COMPLETE)
- Created `app/widgets/markdown.py` — `MarkdownView` widget
- Renders headers, bold, italic, code blocks, inline code, lists, links
- Syntax-highlighted code blocks with dark theme
- Replaces plain QPlainTextEdit in AI chat

### ✅ Feature 5: Inline Diff Viewer (COMPLETE)
- Created `app/widgets/diff_view.py` — `DiffView` widget
- Unified diff with color-coded additions (green) / deletions (red)
- Added `changed_files()` and `show_file()` to `repo/git_manager.py`
- Replaces QMessageBox popup for "What changed?"

### ✅ Feature 6: Session Management (COMPLETE)
- Added search/filter input to sidebar
- Real-time project filtering as user types
- Project list updates dynamically

### ✅ Feature 7: Tool Execution Views (COMPLETE)
- Created `app/widgets/tool_view.py` — `ToolExecutionCard` + `ToolExecutionView`
- Collapsible cards showing command, duration, exit code
- Status indicators (green check / red X)
- Integrated into Run tab alongside output pane

### ✅ Feature 8: Undo/Redo for AI Edits (COMPLETE)
- Added undo/redo buttons to AI tab
- Tracks file changes per AI edit operation
- Full file content restoration on undo/redo
- Clear visual feedback in chat log

### ✅ Feature 9: Model Cycling System (COMPLETE)
Auto-rotates through free-tier AI models with seamless context handoffs.

**Architecture:**
```
ai/cycling.py     — CyclingBackend + UsageTracker classes
ai/providers.py   — 8 free-tier provider definitions
ai/__init__.py    — get_backend() returns CyclingBackend
ai/settings.py    — cycle index persistence
```

**Provider Chain (4 no-key + 4 free-signup):**
| Priority | Provider | Key Required | RPM | RPD |
|----------|----------|-------------|-----|-----|
| 1 | BlockRun | No | 20 | 1000 |
| 2 | OVHcloud | No | 2 | 2880 |
| 3 | uncloseai | No | 10 | 500 |
| 4 | OpenAPIs | No | 10 | 500 |
| 5 | Groq | Free signup | 30 | 1000 |
| 6 | Cerebras | Free signup | 30 | 1M |
| 7 | OpenRouter | Free signup | 20 | 50 |
| 8 | Mistral | Free signup | 30 | 3M |

**How it works:**
1. Editor calls `get_backend()` → gets `CyclingBackend`
2. CyclingBackend tries providers in priority order
3. At 80% rate limit or on error → packages full context → tries next
4. Handoff includes: system prompt + conversation history + project state
5. Next provider receives handoff, continues seamlessly
6. No UI for model selection — fully automatic

**Files created:**
- `ai/providers.py` — `ModelProvider` dataclass + provider list
- `ai/cycling.py` — `CyclingBackend(AIBackend)` + `UsageTracker`

**Files modified:**
- `ai/__init__.py` — `get_backend()` returns `CyclingBackend`
- `ai/settings.py` — `get_cycle_index()` / `set_cycle_index()`
- `app/screens/editor.py` — removed model selector, updated status text

### ⏳ Features 10-14: Polish (AFTER MODEL CYCLING)
| # | Feature | Status |
|---|---------|--------|
| 10 | Attention system (sounds + notifications) | Created `app/notifications.py`, integrated |
| 11 | Session export | Added export button + `_export_session()` |
| 12 | Model selector | REMOVED — replaced by auto-cycling |
| 13 | File attachments | Created `app/widgets/context_panel.py`, integrated in editor |
| 14 | Context panel | Created `app/widgets/context_panel.py`, integrated in editor |

## Files Created This Session
```
app/widgets/__init__.py          (renamed from app/widgets.py)
app/widgets/sidebar.py           (Feature 1: sidebar)
app/widgets/markdown.py          (Feature 4: markdown rendering)
app/widgets/diff_view.py         (Feature 5: diff viewer)
app/widgets/tool_view.py         (Feature 7: tool execution cards)
app/widgets/context_panel.py     (Features 13 & 14: file attachments + context panel)
app/notifications.py             (Feature 10: attention system)
.snapshots/create_savepoint.py   (save point utility)
ai/providers.py                  (Feature 9: model providers)
ai/cycling.py                    (Feature 9: cycling backend)
```

## Files Modified This Session
```
app/main_window.py               (sidebar layout + content area)
app/screens/home.py              (simplified — project list in sidebar)
app/screens/editor.py            (tabs, Build/Plan, markdown, diff, undo/redo, export, cycling status, attachments, context panel)
repo/git_manager.py              (added changed_files, show_file methods)
app/widgets/__init__.py          (export new widgets)
ai/__init__.py                   (get_backend() returns CyclingBackend)
ai/settings.py                   (get_cycle_index / set_cycle_index)
```

## Test Results
```
46 passed, 4 skipped (Kotlin stress tests — kotlinc not installed)
```

## To Pick Up Later
1. Install `kotlinc` to enable Kotlin stress tests
2. All 14 roadmap features complete — project is feature-complete

## Packaging / Distribution (opencode-style install)
- `build_exe.py` — PyInstaller build producing a standalone `dist/Creator.exe`
  (bundles `templates/` via `--add-data`; `app.paths.app_root()` reads
  `sys._MEIPASS` when frozen).
- `install.ps1` — Windows one-liner installer (`irm .../install.ps1 | iex`)
  downloads the latest release `Creator.exe` and adds it to PATH.
- `install.sh` — macOS/Linux equivalent (`curl ... | sh`).
- `app/paths.py` — `app_root()` + `templates_dir()` resolve correctly both from
  source and from the frozen bundle (fixes the old `ROOT` based on `__file__`).
- `pyproject.toml` — minimal packaging with `creator` console entry point.
- README updated with the download/install + build-from-source instructions.
- `templates_dir()` now used by `editor.py` and `wizard.py` (replaced `ROOT /
  "templates"`).

### CRITICAL FROZEN-EXE BUG (fixed 2026-08-14)
**Symptom:** running `dist/Creator.exe` spawned infinitely many windows
(required a hard restart).

**Root cause:** in a PyInstaller bundle `sys.executable` is `Creator.exe`
itself, NOT python. `runners/detector.py:detect_python()` called
`subprocess.run([sys.executable, "--version"])` during startup toolchain
detection (`sidebar.refresh()` -> `detect_all()`), which re-launched the whole
app, which detected again, etc. `runners/python_runner.py` had the same flaw.

**Fix:** both now resolve the real interpreter via `shutil.which("python")` /
`python3` (falling back to `sys.executable` only when NOT frozen). Verified the
rebuilt exe launches one app process + the normal PyInstaller bootloader child
(stable at 2, no growth).

**Rule:** never use `sys.executable` for subprocess calls in code that gets
frozen — use `shutil.which` for the real tool, or guard with
`if not getattr(sys, "frozen", False)`.
