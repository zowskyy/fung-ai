# Creator

**Build things without code.** Pick a kit, answer a few plain-language
questions, and Creator writes the files, runs them, and keeps a version
history for you.

**Get AI for free.** No sign-ups, no keys, no paywalls. Creator cycles through 31+ free-tier AI providers, so you can chat with AI models without ever seeing a "limit reached" message. Want your own key? That works too.

Fully open-source. AI is baked-in and optional—works great with or without it.

## Install it (one line, no Python needed)

Creator ships as a single standalone binary. Pick your OS:

**Windows:**
```powershell
irm https://github.com/thewi/Creator/releases/download/v0.2.0/install.ps1 | iex
```

**macOS / Linux:**
```bash
curl -fsSL https://github.com/thewi/Creator/releases/download/v0.2.0/install.sh | sh
```

Then restart your terminal and type:
```
Creator
```

**Update** — just run the installer again. It grabs the latest release automatically.

**Uninstall** — delete the binary from `%LOCALAPPDATA%\Programs\Creator` (Windows) or `~/.local/bin` (macOS/Linux) and remove that folder from your PATH.

See [RELEASE.md](RELEASE.md) for detailed troubleshooting and maintainer notes.

## Build the binary yourself

```
python build_exe.py      # produces dist/Creator.exe (Windows)
```

Then upload `dist/Creator.exe` to a GitHub Release tagged `latest` so the
install scripts can find it. Edit `install.ps1` / `install.sh` to point at your
repo (`$Repo` / `CREATOR_REPO`).

## Run from source (developers)

Double-click `start.bat`, or:

```
python run.py            start the app
python run.py --learn    guided tour of the codebase
python run.py --test     run the automated tests
```

First run creates `.venv` and installs PySide6 + pytest automatically.

## What's inside

| Piece | Purpose |
|---|---|
| `app/` | PySide6 desktop interface (home, wizard, editor, run, versions) |
| `core/` | Template engine + field models (the no-AI brain) |
| `sandbox/` | Safe per-project workspace with version snapshots |
| `repo/` | Git-based history in plain words: Save / Restore / What changed |
| `runners/` | Toolchain detection + running your creations |
| `ai/` | Optional AI backends (opencode engine or any OpenAI-style server) |
| `templates/` | The starter kits (2d-platformer included) |
| `tests/` | Automated checks |

## Using AI (no sign-ups, no keys needed)

1. In the editor, open the **"Ask AI"** tab.
2. **Just start typing** — Creator automatically rotates through 31+ free-tier AI providers.
3. Never see a rate limit — when one provider hits a limit, Creator seamlessly switches to the next.
4. Your conversation history is saved locally and survives app restart.

**Want your own key?** Set an environment variable (`ANTHROPIC_API_KEY`, `GROQ_API_KEY`, etc.) and Creator will use it alongside the free providers.

**Bring a local model?** Creator also works with Ollama, LocalAI, or any OpenAI-compatible server.

While your response loads, the **"Ideas you might not have thought of"** panel streams related suggestions — inspiration while the AI thinks.

### Letting the AI edit files (experimental, off by default)

Tick **"Let the AI edit my files"** in the Ask AI tab to enable the agent
loop (option C). When on, the AI may propose edits as `%%EDIT` blocks; Creator
snapshots your project first, applies the change, and every change is undoable
from the **Versions** tab. This stays off unless you opt in, so the default
experience is a conversational helper that never touches your files.

Works offline with no AI at all. The template + wizard + run + versions
path is fully functional without any AI.

### Testing the opencode adapter without installing opencode

`tools/opencode_mock_server.py` is a dependency-free server that speaks the
subset of opencode's API Creator uses. Run it, then point the adapter at it:

```
python tools/opencode_mock_server.py --port 8765
set OPENCODE_BASE_URL=http://127.0.0.1:8765
python run.py
```

## Tests

```
python run.py --test
```

The git history wrapper is tested with an in-memory git stand-in so the suite
runs anywhere without spawning a real `git` process. Both AI adapters are tested
against real local HTTP servers (see `tests/test_ai_server.py`).
