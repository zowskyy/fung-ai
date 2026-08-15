# Changelog

All notable changes to the Fung Godot Toolkit are documented in this file.

## 0.1.0 (Unreleased)

Initial functional slice of the Fung Godot Toolkit — a Godot 4 editor
plugin for offline, procedural cave-level generation, driven by a local
Python bridge process.

### Added

- **Godot editor plugin** (`godot_addon/addons/fung_godot/`, `plugin.cfg`
  version `0.1.0`) with a docked Fung panel (`fung_dock.gd`) providing
  three functional tabs:
  - **Generate** — recipe selection, map size, seed (with randomize),
    generation budget (Fast/Balanced/Thorough), and progress display.
  - **Candidates** — browses generated candidates from a completed job,
    with preview image, per-candidate metrics, and tags.
  - **Export** — exports a selected candidate to a `TileMapLayer` scene
    given a `TileSet` resource.
  - "Environment" and "Library" tabs are present as placeholders, not yet
    implemented.
- **`FungBackendClient`** (`services/fung_backend_client.gd`) — job
  lifecycle state machine, Python subprocess invocation
  (`python -m bridge.fung_bridge`), and `status.json` polling.
- **`FungExportService`** (`services/fung_export_service.gd`) — decodes a
  candidate's RLE-encoded grid and builds a `TileMapLayer` + spawn/exit/
  gameplay marker scene, saved via `ResourceSaver`.
- **Local JSON-file bridge protocol** (`bridge/`) — `fung_bridge.py` CLI
  entry point, `bridge/schemas.py` typed request/result/error/status
  models, and `bridge/manifest_writer.py` for atomic JSON writes. See
  `docs/bridge_protocol.md` for the full contract.
- **Generation engine integration** (`bridge/generation.py`) coordinating
  the `fung_ai_v2` cellular-automaton engine: candidate generation,
  connectivity validation, gameplay-facing metrics (walkable ratio, path
  length, loop count, branch count, open space score, composite score),
  tag generation, RLE grid encoding, and preview PNG rendering.
- **Three built-in recipes**: `compact_roguelike_rooms`, `open_exploration`,
  `dense_maze`. See `docs/recipes.md` for their exact parameters.
- **CI**: two GitHub Actions workflows —
  `.github/workflows/test.yml` (Python 3.11, `ruff` lint over
  `fung_ai_v2/`, `bridge/`, `scripts/`, and the `pytest` suite) and
  `.github/workflows/godot_addon.yml` (real headless Godot 4.3.0
  execution: a class-cache import pass, then `tests/test_dock_smoke.gd`,
  which exercises the dock UI tree, backend client, export service, and
  the RLE encode/decode cross-language contract).
- Documentation: `docs/quickstart.md`, `docs/recipes.md`,
  `docs/architecture.md`, `docs/bridge_protocol.md`,
  `docs/troubleshooting.md`.
- Project governance: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, issue and pull request templates.
- `LICENSE` — MIT.
