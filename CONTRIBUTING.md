# Contributing to the Fung Godot Toolkit

Thanks for your interest in contributing. This project is MIT-licensed and
welcomes issues, discussion, and pull requests.

This document covers the Fung Godot Toolkit v0.1 addon and its Python
bridge (`godot_addon/`, `bridge/`, `fung_ai_v2/`). The repository also
contains an older, separate `fung_core/` subsystem with its own CI
workflow (`fung_core.yml`) — if you're working in that area, check its own
docs under `fung_core/docs/` first.

## Running the tests locally

From the repo root, with Python 3.11+ and the dependencies installed:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov ruff

# Lint (matches CI exactly)
ruff check fung_ai_v2/ bridge/ scripts/ --select=E,W,F

# Tests (pytest.ini already configures -v, --strict-markers, and coverage
# reporting for fung_ai_v2/ via addopts)
python3 -m pytest tests/ -q
```

For GDScript, there's a lint helper (originally written for the
`fung_core` addon, but usable here too):

```bash
python3 fung_core/tools/gdscript_lint.py
```

## What CI actually checks

Two workflows gate changes to the toolkit described in this doc:

- **`.github/workflows/test.yml`** ("Tests") — installs Python 3.11 and
  `requirements.txt`, then `pytest`/`pytest-cov`/`ruff`; runs
  `ruff check fung_ai_v2/ bridge/ scripts/ --select=E,W,F` followed by
  `python -m pytest --tb=short`. This is the gate for anything under
  `bridge/` or `fung_ai_v2/`.
- **`.github/workflows/godot_addon.yml`** ("Fung Godot Toolkit Addon") —
  installs a real Godot `4.3.0` headless binary
  (`chickensoft-games/setup-godot@v2`), runs an editor import pass first
  (`godot --headless --editor --quit --path godot_addon`, needed so
  `class_name` scripts like `FungDock`/`FungBackendClient` are registered
  before the test runs), then runs the smoke test:
  `godot --headless --path godot_addon -s tests/test_dock_smoke.gd`. This
  is the gate for anything under `godot_addon/addons/fung_godot/`.

## Working on GDScript without a local Godot binary

Most development sandboxes here don't have a Godot binary available, so
GDScript changes can't always be run locally before opening a PR. In that
situation:

- Follow the patterns already established in the addon's existing files —
  `godot_addon/addons/fung_godot/services/fung_backend_client.gd` is a good
  reference for this codebase's conventions (typed member variables,
  `@tool` + `class_name` at the top, signals declared up front, JSON
  helpers as small private methods, etc.).
- Don't assume a change is correct just because it reads correctly and
  matches those patterns. `godot_addon.yml` is the actual, authoritative
  check — its comments note that it is "the first real execution" of code
  written without a local Godot binary available, and real bugs have been
  caught there before (see the git history around
  `Fix Godot addon UI construction bugs and add real headless CI for it`
  and `Fix smoke test timing: run setup/assertions from _process(), not
  _initialize()`). Push your change and check the workflow run rather than
  treating "it compiles in my head" as done.
- If you're adding new behavior, add or extend assertions in
  `godot_addon/tests/test_dock_smoke.gd` so the CI gate actually exercises
  what you changed.

## Adding or changing a recipe

See `docs/recipes.md` for the current recipe list and
`.github/ISSUE_TEMPLATE/recipe_submission.md` for what a community recipe
submission should include (recipe id, `rule_string`, density, steps,
fitness targets, a deterministic seed with expected metric ranges, and
license/attribution).

## Pull requests

Please use `.github/pull_request_template.md` (it's picked up
automatically when you open a PR). Keep PRs scoped — this repo has learned
the hard way (see the Phase-by-phase commit history) that small, verifiable
steps checked against real CI beat large unverified ones.
