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
| `ca_bridge.gd` | Subprocess bridge: calls fung-ai-v2 CLI, reads JSON scene output (portable Python detection) | complete |
| `tilemap_painter.gd` | TileMapLayer renderer (replaces ColorRect prototype) | complete |

---

## Scene Animator addon: `godot_project/addons/scene_animator/`

**Purpose:** Deterministic, data-driven cutscene/scene sequencer for Godot 4.7.1.
A `ScenePlan` resource describes a sequence of beats (dialogue, movement,
actions, camera, encounters, branching); a headless-safe `SceneDirector` drives
the plan against the scene through a `SceneActorAdapter` layer. Ships an editor
plugin (dock + inspector), an authoring validator, a runnable demo, and a
headless test/CI gate. Delivered in phases 0–6, each gated green.

### File inventory (`godot_project/addons/scene_animator/`)

| File / dir | Purpose | Status |
|------------|---------|--------|
| `plugin.cfg`, `plugin.gd` | Editor plugin (dock + inspector), idempotent add/remove | complete |
| `data/scene_plan.gd` | `ScenePlan` root resource (beats, actors, capability registry) | complete |
| `data/scene_beat.gd` | `SceneBeat` base (`next_beat_id`, `failure_beat_id`, `enabled`) | complete |
| `data/scene_actor_binding.gd` | `SceneActorBinding` authoring metadata (id, tags, path) | complete |
| `data/scene_capability_registry.gd` | Registered actions/cameras/encounters/conditions | complete |
| `data/action_definition.gd` | Action def + tag matching | complete |
| `data/camera_mode_definition.gd` | Camera mode def (focus requirement) | complete |
| `data/encounter_definition.gd` | Encounter def | complete |
| `data/condition_definition.gd` | Condition def | complete |
| `data/interaction_definition.gd` | Interaction def | complete |
| `data/beats/*.gd` | 12 beat subtypes (dialogue, move_to, look_at, action, camera, wait, wait_for_event, set_state, spawn_encounter, branch, end) | complete |
| `runtime/scene_director.gd` | Deterministic sequencer (`scene_started/finished/failed`) | complete |
| `runtime/scene_bindings.gd` | Actor/named-node resolver (`actor_nodes`, `named_nodes`) | complete |
| `runtime/scene_actor_adapter.gd` | Actor contract + deadline defaults | complete |
| `runtime/placeholder_actor_adapter.gd` | Drop-in actor with Marker3D body for demos | complete |
| `runtime/scene_camera_adapter.gd` | Camera contract | complete |
| `runtime/scene_mechanics_registry.gd` | Effect/encounter/camera/state/condition hooks by ID | complete |
| `runtime/beat_runner.gd` + `runtime/runners/*.gd` | Per-beat runners (12) | complete |
| `editor/scene_plan_dock.gd` | Dock UI: load plan, actors/beats tree, validate, issues | complete |
| `editor/inspectors/scene_plan_inspector.gd` | Inspector "Validate Scene Plan" button | complete |
| `editor/validators/validation_issue.gd` | `ScenePlanValidationIssue` (severity/code/details) | complete |
| `editor/validators/scene_plan_validation_result.gd` | Validation result (is_valid, issue_codes) | complete |
| `editor/validators/scene_plan_validator.gd` | All `scene_animator.validation.*` rules | complete |
| `demo/demo_scene.gd`, `demo_scene.tscn`, `demo_scene_plan.tres` | Runnable 3-line dialogue demo | complete |
| `templates/starter_scene_plan.tres` | Blank starter plan | complete |
| `tests/gate.sh` | Canonical gate: import -> parse_check -> runner | complete |
| `tests/parse_check.gd` | Loads every addon script/resource; manifest coverage guard | complete |
| `tests/run_scene_animator_tests.gd` | Suite runner, prints `SCENE_ANIMATOR_RESULT: {json}`, exit 0/1/2 | complete |
| `tests/test_runtime_execution.gd` | Runtime contract suite (fixtures + programmatic plans) | complete |
| `tests/test_plugin_activation.gd` | Editor-boot activation subprocess test | complete |
| `tests/test_validators.gd` | Validator rule coverage (programmatic + fixtures) | complete |
| `tests/test_demo_execution.gd` | Demo end-to-end + template validity | complete |
| `tests/fixtures/*.tres` | valid_linear + 4 invalid plans (missing speaker, unknown target, duplicate beat ids, dangling next) | complete |
| `tests/support/*.gd` | Test harness (context/result) + fakes (actor, camera, mechanics) | complete |
| `README.md` | Addon documentation | complete |

### Success contract (all verified green)

- Canonical gate (headless, Godot 4.7.1): import + parse check (59 scripts +
  8 resources) + 4 suites / 99 assertions, exit 0. CI on `origin/scene-animator`
  green (SHA-256-pinned Godot 4.7.1, artifact upload, hygiene check).
- Editor boot (`--headless --editor --quit-after 3`) exits 0; `project.godot`
  stays at features 4.3 (import does not rewrite it); `.godot/` is gitignored.

### Open dependencies

None — all wired-in modules exist and pass the gate.

### Known gaps

- BranchBeat / camera / encounter / action runner behaviors are covered at the
  authoring-validator level; full runtime smoke for every beat type is future
  work (dialogue is the exercised end-to-end path).
- The plugin dock/inspector are covered by structure + activation checks, not
  pixel assertions; interactive usability is verified by launching the editor.

---

## Open Dependencies

None — all referenced modules exist and tests pass.

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
| W8 GodotBridge | ca_bridge.gd (portable Python detection) | complete |
| W9 TileMapRenderer | tilemap_painter.gd | complete |
| W10 GitHubRelease | README, license, examples, v0.1.0 tag | in-progress |
