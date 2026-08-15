# CI Architecture & Design Decisions

This document explains the GitHub Actions CI/CD configuration for Fung and the reasoning behind key architectural choices.

## Workflow Overview

Three independent workflows handle different aspects of the codebase:

### 1. Tests (`test.yml`)
**Purpose:** Python validation suite (bridge, generation, validators, exporters)

**Jobs:**
- Lint check (ruff): Code style and basic correctness
- Python tests (pytest): Unit tests (257+ tests covering CA engine, RLE encoding, schema validation)

**Timeout:** 5 minutes per job
**Node:** ubuntu-latest with Python 3.11

**Rationale:**
- Python code is deterministic and can run without Godot
- Separates Python validation (fast, always required) from Godot validation (slower, heavyweight)
- Enables parallel execution with other workflows

### 2. Fung Core (`fung_core.yml`)
**Purpose:** Core addon runtime validation (Godot + Python integration)

**Jobs:**
- **python-checks**: Python validators for JSON schemas, example validation, GDScript linting
- **godot-checks**: Godot headless tests for Narrative systems (CutsceneDirector), JSON Schema conformance, vertical-slice example execution, and determinism verification (replay check)

**Timeout:** 10 minutes per job
**Node:** ubuntu-latest with Godot 4.3.0

**Rationale:**
- Validates that Fung Core addon loads and core systems work end-to-end
- Uses deterministic test seeds (seed=42) for reproducibility
- Artifact upload (replay.json) enables post-hoc analysis
- Headless-only (no DisplayServer needed for core validation)

### 3. Fung Godot Toolkit Addon (`godot_addon.yml`)
**Purpose:** v0.1 plugin validation (editor plugin, export service, sample projects)

**Jobs:**
- **godot-checks**: Addon smoke test (dock UI, backend client, export service)
- **sample-projects-checks**: Boot-test for all three sample projects (roguelike, exploration, metroidvania)

**Timeout:** 5 minutes per job (addon smoke test), 5 minutes per job (sample matrix)
**Node:** ubuntu-latest with Godot 4.3.0

**Rationale:**
- Validates plugin loads in real Godot project
- Sample project matrix ensures all three game-ready examples work end-to-end
- Early error detection: CI is the first real execution of GDScript (no local Godot binary in dev environment)
- Parses Godot output explicitly for errors (Godot doesn't always fail exit code on script errors)

## Key Architectural Decisions

### Why Headless-Only (No xvfb-run)?

The current CI uses Godot's `--headless` flag exclusively. This is correct for v0.1 because:

1. **Core systems don't require rendering:** CutsceneDirector, WorldLoader, EntityRegistry, AnimationController are all data-driven and work without a DisplayServer
2. **Sample projects are headless-compatible:** Boot-check exercises JSON loading, RLE decoding, TileMapLayer construction, procedural TileSet generation, and player spawn—all non-rendering code paths
3. **Camera2D.current edge case handled:** Sample projects guard `Camera2D.current = true` behind `if DisplayServer.get_name() != "headless"` check. This preserves real editor/gameplay behavior while allowing CI boot-check to complete

**Future consideration:** If editor-feature tests are added (e.g., dock UI widget assertions, visual preview validation), those would require xvfb-run (simulated X11 display). This is deferred post-v0.1.

### Why Not A Persistent Python Worker?

The bridge uses a JSON-file protocol (request.json → result.json) rather than a persistent background process because:

1. **Isolation:** Each job gets its own clean environment; no state leakage between runs
2. **Headless-friendly:** Works in CI, Docker, user's project directory without setup overhead
3. **User-visible**: Job directory and manifests are human-readable; easier debugging
4. **Simple subprocess model:** `OS.create_process()` + file polling is simpler than socket communication
5. **Cancellation:** Cooperative cancel via `cancel.request` file + forced `OS.kill()` on timeout

See `docs/bridge_protocol.md` for the full JSON contract.

### Why Timeout Guards?

Explicit `timeout` wrappers around each Godot invocation provide:

1. **Detectability:** If a process hangs, timeout exits with code 124 (SIGALRM), which is unambiguous
2. **Isolation:** Process-level timeouts fire even if job timeout is misconfigured
3. **Accountability:** Makes expected duration explicit in code

Timeout values chosen based on observed performance:
- Import project (first run, builds class cache): 60s
- Addon smoke test: 60s
- Sample project boot-check: 90s (slower, runs 3 samples in matrix)
- Conformance tests (comprehensive JSON validation): 120s
- Replay check: 60s

## Godot Binary Caching

Uses `chickensoft-games/setup-godot@v2` which:
- Caches Godot binary by version/OS/arch
- Skips re-download on cache hits
- Handles dotnet dependency management

No additional caching configuration needed; chickensoft action handles it transparently.

## Future Enhancements

### Post-v0.1 Improvements (not blocking release):

1. **Structured test reporting**
   - JSON test result objects for CI dashboards
   - Per-test timing and resource usage
   - Artifact uploads of test logs

2. **GUI editor tests (with xvfb-run)**
   - Dock UI widget assertions
   - Export preview visualization validation
   - Recipe UI interaction tests
   - Requires: `apt install xvfb`, wrap Godot with `xvfb-run`

3. **Performance budgets**
   - Assert generation time < 100ms per candidate
   - Assert export time < 500ms
   - Memory usage tracking

4. **Flake detection**
   - Rerun failing tests automatically
   - Report flaky test rate
   - Flag non-deterministic tests

5. **Coverage reporting**
   - GDScript code coverage for addon
   - Python coverage for bridge/validators
   - Coverage trends over time

## Debugging CI Failures

### When a sample project boots fails:

1. Check the Godot output log for SCRIPT ERROR / PARSE ERROR / ERROR: lines
2. Sample logs include full stack traces; search for the file:line reference
3. Note: Godot may log errors but still exit 0; grep checking in CI catches this

Example failure pattern (now fixed):
```
ERROR: res://player.gd:1:1 - Invalid assignment of property or key 'current'
```

### When Python tests fail:

1. `pytest` output includes full traceback
2. Ruff errors show line/column and specific violation code
3. Both respect `--tb=short` for readability

### Workflow-level issues:

1. Check chickensoft-games/setup-godot logs for binary download/cache issues
2. Check actions/setup-python logs for dependency install issues
3. For matrix failures, check if issue is per-sample or global

## CI Maintenance

### Adding a new test:

1. Write test script (e.g., `test_new_feature.gd` or `test_new_feature.py`)
2. Add step to appropriate workflow
3. Set appropriate timeout based on complexity
4. Run workflow and verify it passes before merging

### Updating Godot version:

1. Update version in `godot-checks` setup steps
2. Test locally if possible
3. Monitor for new Godot-specific errors
4. Document any API changes or workarounds

### Disabling/skipping tests:

Use GitHub Actions conditions:
```yaml
- name: Conditional test
  if: always()  # or: if: failure() to run only after failure
  run: ...
```

Prefer explicit conditions over `continue-on-error`, which masks real failures.

## Cost & Duration

Current typical CI run time (3 workflows in parallel):
- **Tests** (pytest + ruff): ~30-45 seconds
- **Fung Core** (python-checks + godot-checks): ~60-90 seconds
- **Godot Addon** (addon smoke test + 3-sample matrix): ~120-150 seconds

**Total:** ~2-2.5 minutes for full CI on push

All runs on GitHub's free tier; no resource cost.

---

Last updated: 2026-08-15
