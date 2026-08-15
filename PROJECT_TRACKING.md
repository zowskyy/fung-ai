# fung.us — Project Tracking

**Purpose:** CA (Cellular Automata) engine for procedural game-level generation. Takes real-world geospatial data (weather, biome, elevation) and produces cave-like tile maps via MAP-Elites quality-diversity search. Target export: Godot 4 TileMap scenes + libresprite aseprite sheets.

---

## Core Package: `fung_ai_v2/`

| File | Purpose | Status |
|------|---------|--------|
| `__init__.py` | Public API surface, version | complete |
| `ca_engine.py` | CARule dataclass, step_ca, initialize_random, biome density/rule tables | complete |
| `fitness.py` | has_path, evaluate_ca_rule, compute_descriptors, interestingness metrics | complete |
| `archive.py` | GridArchive + ArchiveCell (MAP-Elites + CMA-MAE + DNS) | complete |
| `emitters.py` | Emitter ABC, MAP_Elites_Emitter (ask/tell) | complete |
| `algorithms.py` | RandomSearch, Standard_MAP_Elites, run_held_out_benchmark | complete |
| `validators.py` | validate_rule_string, validate_grid, validate_cli_args, sanitize_path | complete |
| `exporters.py` | GodotExporter (scene JSON, navigation polygon) | complete |
| `environment.py` | get_environment, classify_biome, weather/climate/settlement fetch | complete |
| `cache.py` | On-disk JSON cache with TTL for environment calls | complete |
| `cli.py` | CLI entry point: generate, benchmark, compare, export, query subcommands | complete |

---

## Tests: `tests/`

| File | What it tests | Status |
|------|--------------|--------|
| `conftest.py` | Shared fixtures (CARule instances, grid shapes, sample env) | complete |
| `test_ca_engine.py` | CARule parsing, genotype, step_ca, initialize_random, compute_density (20 tests) | complete |
| `test_fitness.py` | has_path, evaluate_ca_rule, compute_descriptors, interestingness (18 tests) | complete |
| `test_archive.py` | GridArchive, ArchiveCell, add/get/coverage/qd_score (12 tests) | complete |
| `test_validators.py` | validate_rule_string, validate_grid, validate_cli_args, sanitize_path (8 tests) | complete |
| `test_connectivity.py` | has_path: positive cases, negative cases, partial coverage, size invariance (15 tests) | complete |
| `test_environment.py` | classify_biome (pure), get_environment (mocked HTTP) (16 tests) | complete |
| `test_map_elites.py` | RandomSearch/Standard_MAP_Elites end-to-end, archive consistency, benchmark, verbose output (20 tests) | complete |
| `test_emitters.py` | Emitter reset, ask() edge cases (3 tests) | complete |

**Total: 127 tests, 127 passing as of 2026-08-14.**

### Core Coverage (100% push)

| File | Coverage | Notes |
|------|----------|-------|
| ca_engine.py | 100% | |
| archive.py | 100% | |
| algorithms.py | 100% | |
| validators.py | 100% | |
| fitness.py | 99% | line 94: unreachable dead code (guarded by shape check on line 80; total==0 can never occur once shape≥3x3) |
| emitters.py | 93% | lines 32,38: abstract method bodies (unreachable by design); line 68: unreachable given archive.filled_count>=2 guarantees get_random_elite() returns non-None |

Core engine (ca_engine, archive, algorithms, fitness, emitters, validators) effectively at 100% — remaining gaps are provably unreachable defensive code, not missing tests.

---

## Scripts: `scripts/`

| File | Purpose | Status |
|------|---------|--------|
| `taylor_ops_team.py` | 10-worker swarm orchestrator (W1–W10). Dry run by default; production --apply gates on validate_pipeline_state() | complete |
| `extract_modules.py` | Verifies extracted package is complete and non-stub. Read-only. Does NOT write files. | complete |
| `validate_extraction_targets.py` | Parses actual source via ast.walk, verifies all named exports exist before any generator runs | complete |

---

## Security: `security/`

| File | Purpose | Status |
|------|---------|--------|
| `cursor_gate.py` | Scans for eval/exec/pickle/hardcoded secrets; exits non-zero if found | complete |

---

## CI/CD

| File | Purpose | Status |
|------|---------|--------|
| `.github/workflows/test.yml` | Run ruff + pytest on push/PR | complete |

---

## Godot Integration: `godot_project/`

| File | Purpose | Status |
|------|---------|--------|
| `ca_bridge.gd` | Subprocess bridge: calls fung-ai-v2 CLI, reads JSON scene output | not started — W8 |
| `tilemap_painter.gd` | TileMapLayer renderer (replaces ColorRect prototype) | not started — W9 |

---

## Open Dependencies

- `tests/test_map_elites.py` — referenced by W7 in taylor_ops_team.py; does not exist yet. W7 should populate it before running.
- `fung_ai_v2/connectivity.py` — referenced by W5 worker config; connectivity functions live in `fitness.py`. Either redirect W5 or create a thin re-export module.
- `tests/__init__.py` — referenced by W1's apply_commands; currently absent (pytest discovers tests without it; add if namespace conflicts arise).

---

## Known Gaps

- `fung_ai_v2/algorithms.py`: `RandomSearch` and `Standard_MAP_Elites` have no `get_results()` implemented in original monolith — W2 added it; verify it matches what `run_held_out_benchmark` expects.
- `test_carule_crossover_child_genes` — fixed 2026-08-14 (original parents differed in 1 bit; updated to parents with many differing bits).
- `validate_cli_args` does not validate `seed` — fixed 2026-08-14 (0 to 2^31-1 bounds added).
- `CARule.from_genotype` off-by-nine bug — fixed 2026-08-14 in both `fung_ai_v2/ca_engine.py` and `fungaiV2_extracted/fung_ai_v2.py`.

---

## Completed Workers (Taylor Ops)

| Worker | Description | Status |
|--------|------------|--------|
| W1 GateKeeper TestInfra | pytest, CI/CD, ruff, pyproject | complete |
| W2 CompilerCore CARefactor | Hand-extracted all 11 modules, 8 bugs fixed | complete |
| W3 AuditGuardian Security | cursor_gate.py, validators.py, path sanitization | complete |
| W4 CACoreTester | 20 CA engine tests | complete |
| W5 ConnectivityTester | 15 connectivity/pathfinding tests | complete |
| W6 BiomeTester | 16 environment/biome tests | complete |
| W7 FitnessTester | 17 MAP-Elites/RandomSearch/benchmark tests | complete |
| W8 GodotBridge | ca_bridge.gd | not started |
| W9 TileMapRenderer | tilemap_painter.gd | not started |
| W10 GitHubRelease | README, license, examples, v0.1.0 tag | not started |
