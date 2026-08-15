# Creator Release & Distribution Guide

**Version**: v0.2.0  
**Status**: Ready for Distribution  
**Build Date**: 2026-08-14

---

## Quick Start (For End Users)

### Windows (One-Liner)
```powershell
irm https://github.com/thewi/Creator/releases/download/v0.2.0/install.ps1 | iex
```

Then restart your terminal and run:
```
Creator
```

### macOS / Linux (One-Liner)
```bash
curl -fsSL https://github.com/thewi/Creator/releases/download/v0.2.0/install.sh | sh
```

Then run:
```
Creator
```

---

## For Maintainers: How to Release

### Step 1: Build the Standalone Executable
```bash
python build_exe.py
```

This produces `dist/Creator/Creator.exe` (Windows) which bundles:
- All Python dependencies (PySide6, pytest, etc.)
- All templates (2d-platformer, language templates)
- No Python installation required

**Check the build**:
```bash
dist/Creator/Creator.exe
# Should launch the app with a single window (single-instance guard working)
```

### Step 2: Test the Frozen Exe

Manual testing checklist:
- [ ] Launch exe, create a project, run it
- [ ] Save version, restore version
- [ ] Ask AI a question (if AI key configured)
- [ ] Test file attachment
- [ ] Verify no crashes, no multi-spawn

### Step 3: Create GitHub Release

1. Go to: https://github.com/thewi/Creator/releases/new
2. Tag: `v0.2.0` (or latest version)
3. Title: `Creator v0.2.0 - Seamless AI + Hardened`
4. Description:
   ```markdown
   ## What's New
   - 31+ free-tier AI providers (seamless cycling)
   - Conversation history persists across restarts
   - Smart context windowing for long chats
   - Provider health checking + uptime tracking
   - Much more robust error handling
   
   ## Installation
   **Windows**: `irm https://github.com/thewi/Creator/releases/download/v0.2.0/install.ps1 | iex`
   **macOS/Linux**: `curl -fsSL https://github.com/thewi/Creator/releases/download/v0.2.0/install.sh | sh`
   
   ## Test Results
   - 46 tests passing, 4 skipped (Kotlin)
   - 18 new context persistence tests: all passing
   - 31 AI providers registered and tested
   ```

5. **Upload Assets**:
   - `dist/Creator/Creator.exe` (Windows binary)
   - `install.ps1` (PowerShell installer)
   - `install.sh` (Bash installer)

6. Publish Release

### Step 4: Update Documentation

Update README.md with latest version number and links:
```markdown
## Install it (like opencode)

Creator ships as a single standalone binary — no Python needed.

**Windows (one line):**
\`\`\`
irm https://github.com/thewi/Creator/releases/download/v0.2.0/install.ps1 | iex
\`\`\`

**macOS / Linux (one line):**
\`\`\`
curl -fsSL https://github.com/thewi/Creator/releases/download/v0.2.0/install.sh | sh
\`\`\`
```

### Step 5: Verify Installers Work

Test on clean machines (or in Docker/VMs):

**Windows**:
```powershell
# Run in new PowerShell window
irm https://github.com/thewi/Creator/releases/download/v0.2.0/install.ps1 | iex
Creator
```

**macOS/Linux**:
```bash
# Run in new terminal
curl -fsSL https://github.com/thewi/Creator/releases/download/v0.2.0/install.sh | sh
Creator
```

Both should:
1. Download the binary
2. Add to PATH
3. Launch successfully on first run

---

## What's Included in the Release

### Binary
- **Creator.exe** (~50-100MB): Standalone Windows executable
  - Includes Python 3.14
  - All dependencies bundled
  - Single-instance guard (no multi-spawn)
  - Fast launch (~1s)

### Installers
- **install.ps1**: Windows PowerShell one-liner
  - Auto-detects latest release
  - Adds to PATH
  - Works without admin privileges (installs to AppData)

- **install.sh**: macOS/Linux bash one-liner
  - Auto-detects OS and downloads right binary
  - Adds to ~/.local/bin
  - Makes executable

### Templates Bundled
- 2D Platformer Game (customizable)
- Python Number Guessing Game
- Java Number Guessing Game
- Rust Number Guessing Game
- C++ Number Guessing Game
- JavaScript/Node.js Number Guessing Game

---

## Troubleshooting Installation

### "PowerShell is disabled"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
irm https://github.com/thewi/Creator/releases/download/v0.2.0/install.ps1 | iex
```

### "Command not found: Creator"
Restart your terminal. If still missing:
```powershell
# Windows
$env:Path -split ";" | findstr "Creator"
```

### Installer script fails
Check your internet connection, then try again:
```bash
curl -fsSL https://github.com/thewi/Creator/releases/download/v0.2.0/install.sh -v | sh
```

---

## Versioning & Updates

Creator follows [Semantic Versioning](https://semver.org/):
- **v0.x.y**: Pre-release (features may change)
- **v1.0.0+**: Stable (backwards compatibility guaranteed)

### How Users Update
Simply run the installer again:
```powershell
irm https://github.com/thewi/Creator/releases/download/latest/install.ps1 | iex
```

The script auto-detects the latest release and installs over the old version.

---

## Optional: macOS Signing & Notarization

For production macOS distribution, code sign and notarize:

```bash
# Sign the binary
codesign -s - dist/Creator/Creator

# Notarize for Gatekeeper
xcrun altool --notarize-app -f dist/Creator/Creator ...
```

This ensures macOS users don't get "unidentified developer" warnings.

For now, users can bypass with: `xattr -d com.apple.quarantine Creator`

---

## Next Release Checklist

- [ ] Run `python run.py --test` (all tests pass)
- [ ] Build with `python build_exe.py`
- [ ] Test frozen exe manually
- [ ] Create GitHub release with version tag
- [ ] Upload Creator.exe + install scripts
- [ ] Update README with new version
- [ ] Test installers on clean machines
- [ ] Announce on social media / communities
