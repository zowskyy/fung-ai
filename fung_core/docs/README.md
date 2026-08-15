# Fung Core

Fung Core is a modular Godot 4.x addon plus Python tooling, built inside the
`fung-ai` repo, that turns validated JSON content into game behavior.
Designers author world, entity, encounter, narrative, and animation data as
JSON; Python tooling validates that data against JSON Schemas; a Godot
addon loads the validated data at runtime and drives world generation,
encounters, cutscenes, animation, and replay recording.

## Pipeline

`WorldGenerationJob` → `WorldLoader` → `EncounterSpawner` → `CutsceneDirector`
→ `AnimationController` → `ReplayRecorder`

Each stage consumes JSON content validated against a schema in `contracts/`
and hands off to the next. The `examples/cave_boss/` scene is the reference
vertical slice exercising the full pipeline end to end.

## Directory map

- `contracts/` — JSON Schemas for world, entity, encounter, narrative,
  animation manifest, replay, and project content.
- `godot_addon/fung_core/` — the Godot 4 addon: systems (`systems/core`,
  `systems/world`, `systems/entities`, `systems/narrative`,
  `systems/animation`, `systems/async`, `systems/persistence`), editor
  tooling, and GDScript smoke tests.
- `python/fung_tools/` — Python validators, exporters, and supporting
  tooling for the JSON content pipeline.
- `examples/cave_boss/` — the reference vertical-slice example (content
  JSON, scene, script, and recorded replay).
- `tools/` — headless runners and static checkers (`run_example.gd`,
  `replay_check.gd`, `validate_examples.py`, `gdscript_lint.py`).
- `project.godot` — makes `fung_core/` a self-contained, headless-runnable
  Godot 4 project root.
- `gate.json` — machine-readable gate manifest: required versions, the
  canonical check commands, soft performance budgets, and expected
  artifacts.

## Verification status

**Python side: proven.** Schemas, validators, and exporters under
`python/fung_tools/` are covered by the pytest suite in
`python/tests/`, currently **17/17 tests passing**, independently
re-run multiple times.

**Godot side: reviewed, not executed.** Everything under
`godot_addon/fung_core/systems/`, the `CutsceneDirector`, the
`WorldGenerationJob`, the `examples/cave_boss/` scene, and both
`tools/*.gd` runners (`run_example.gd`, `replay_check.gd`) have been
carefully hand-reviewed for API correctness, but **no line of this
GDScript has ever been executed by the actual Godot engine** anywhere in
this project's development. The dev sandbox that built this addon had no
way to obtain a Godot 4.x binary: apt only ships Godot 3, GitHub releases
were blocked by network policy, and there was no snap, flatpak, or working
Docker daemon available.

The `godot-checks` job in `.github/workflows/fung_core.yml` is the first
place any of this Godot code will actually run. Until that job has gone
green at least once, treat every Godot-side claim in this document (and in
code comments elsewhere in `fung_core/`) as "reviewed, not executed."

## Running everything locally

Requires Python 3.11+ and, for the Godot-side commands, Godot 4.3+ on
`PATH`. All commands below are run from the repo root and are also listed
in `gate.json`.

```
# Python
python3 -m pytest fung_core/python/tests/ -v
python3 fung_core/tools/validate_examples.py
python3 fung_core/tools/gdscript_lint.py

# Godot (requires Godot 4.3+)
godot --headless --path fung_core -s godot_addon/fung_core/tests/test_cutscene_director.gd
godot --headless --path fung_core -s tools/run_example.gd --seed=42 --timeout=30
godot --headless --path fung_core -s tools/replay_check.gd
```

## Phase 9: Native JSON Schema Engine

**Status: In Progress**

Fung Core now includes a native GDScript JSON Schema validation engine that
validates game data at runtime without any Python dependencies. The engine
supports JSON Schema Draft 2020-12 with full keyword support planned across
future phases.

**Key Components:**
- `JsonSchemaAsset` — Resource-based schema storage with compilation caching
- `CompiledSchema` — Runtime-optimized validation execution
- `SchemaNode` — Node-based validator with signal-based error handling
- `ValidationResult` — Detailed error tracking with JSON path information

**Usage Example:**
```gdscript
var schema := JsonSchemaAsset.new(schema_dict)
var result := schema.validate(world_data)
if result.success:
    print("Data is valid!")
else:
    print("Errors: %s" % result.errors)
```

**RFC 8785 Canonicalization:** Schemas use canonical JSON representation for
deterministic validation and reproducible replay recording.

**Documentation:** See [JSON_SCHEMA.md](JSON_SCHEMA.md) for comprehensive API
reference, examples, integration patterns, performance notes, and migration
guide for schema versioning.
