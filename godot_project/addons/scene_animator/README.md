# Scene Animator (Godot 4.7.1)

Deterministic, data-driven cutscene / scene sequencer for Godot 4. A **ScenePlan**
resource describes a sequence of **beats** (dialogue, movement, actions, camera,
encounters, branching); a headless-safe **SceneDirector** drives that plan
against your scene through a small adapter layer. Author in the editor, verify
with the validator, and run the same plan in tests and CI.

Target engine: **Godot 4.7.x stable** (developed and CI-verified on 4.7.1).
Requires no external assets or services.

---

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [Concepts](#concepts)
- [Beat reference](#beat-reference)
- [Runtime wiring](#runtime-wiring)
- [Validation](#validation)
- [Tests and CI](#tests-and-ci)
- [Repository layout](#repository-layout)

---

## Installation

1. Copy the `scene_animator/` directory into your project's `addons/` folder.
2. Enable the plugin in **Project > Project Settings > Plugins**
   ("Scene Animator").
   The plugin adds:
   - a **Scene Animator** dock (bottom-left panel): load a plan, inspect its
     actors/beats, run validation, and see issues.
   - an **Inspector** button ("Validate Scene Plan") on `ScenePlan` resources.
3. The editor plugin is optional. The runtime and validator are plain
   `class_name` scripts and work with the plugin disabled.

The plugin ships pre-enabled in this repository's `project.godot`.

---

## Quick start

Run the included demo scene directly:

```
godot --path godot_project --headless res://addons/scene_animator/demo/demo_scene.tscn
```

Expected output (three chained dialogue lines, then a clean exit):

```
[scene_animator:demo] Hero: "Welcome to the Quiet Cave."
[scene_animator:demo] Hero: "That shadow there? That is the Keeper."
[scene_animator:demo] Keeper: "Leave the amber. Leave, and stay alive."
[scene_animator:demo] Scene finished after 3 dialogue line(s).
```

Start a new plan from `templates/starter_scene_plan.tres`, or author one by hand
following `demo/demo_scene_plan.tres`.

---

## Concepts

| Term | Role |
|------|------|
| `ScenePlan` | Root resource. `plan_id`, `display_name`, `description`, optional `capabilities` registry, `actors` (authoring metadata), `beats`. |
| `SceneBeat` | Base beat. `beat_id`, `enabled`, `next_beat_id` (success), `failure_beat_id` (fallback). |
| `SceneActorBinding` | Authoring entry: stable `actor_id` + semantic `actor_tags` + optional node path. **Authoring metadata only** — the runtime resolves actors from `SceneBindings`, not from this list. |
| `SceneBindings` | Runtime resolver (`actor_nodes` / `named_nodes` maps of `StringName` -> `NodePath`). Returns `SceneActorAdapter`s for beat actors. |
| `SceneDirector` | The sequencer. Walks the first enabled beat, then `next_beat_id` / `failure_beat_id` / branch targets until the plan ends. Emits `scene_started`, `scene_finished`, `scene_failed(reason, details)`. A plan reaches exactly one terminal state. |
| `SceneMechanicsRegistry` | Optional runtime registry of effect hooks (dialogue lines, encounter spawners, camera providers, state setters, condition evaluators) keyed by stable ID. |
| `SceneCapabilityRegistry` | Authoring-time registry of allowed actions / camera modes / encounters / conditions, consumed by the validator and by `@tool` runners. |

**Actor resolution contract.** Dialogue beats resolve the speaker via
`SceneBindings.get_actor(speaker_actor_id)` and the optional target via
`target_actor_id`. An empty `target_actor_id` yields a `null` target (allowed);
a non-empty id that fails to resolve fails the beat with
`scene_animator.missing_target_actor`. A missing speaker fails with
`scene_animator.missing_speaker_actor`. Effect payloads expose
`speaker`, `target_actor`, and `scene_beat_id`.

---

## Beat reference

| Beat | Data (`data/beats/`) | Runner (`runtime/runners/`) | Behavior |
|------|----------------------|-----------------------------|----------|
| Dialogue | `DialogueBeat` | `DialogueBeatRunner` | Resolves speaker/target, plays `dialogue_id` effect on the mechanics registry, waits for the speaker's `action_event_emitted` (`dialogue_finished` or the dialogue id) or times out. |
| Move to | `MoveToBeat` | `MoveToBeatRunner` | `actor_id` moves to a `NodePath` target with arrival radius + locomotion mode; completes on `destination_reached`. |
| Look at | `LookAtBeat` | `LookAtBeatRunner` | `actor_id` looks at a `NodePath` target; completes on `look_at_completed`. |
| Action | `ActionBeat` | `ActionBeatRunner` | `actor_id` performs `action_id` via `request_action`; completes on `action_completed`, fails on `action_failed`/timeout. |
| Camera | `CameraBeat` | `CameraBeatRunner` | Acquires a camera for `camera_mode_id` via the bindings' camera adapter or mechanics registry. |
| Wait | `WaitBeat` | `WaitBeatRunner` | Pauses for `duration_seconds`. |
| Wait for event | `WaitForEventBeat` | `WaitForEventBeatRunner` | Waits for a named `event_name` broadcast (registry event or bindings/actors). |
| Set state | `SetStateBeat` | `SetStateBeatRunner` | Applies `state_id` to a target node via the mechanics registry. |
| Spawn encounter | `SpawnEncounterBeat` | `SpawnEncounterBeatRunner` | Spawns `encounter_id` via the mechanics registry at the given markers. |
| Branch | `BranchBeat` | `BranchBeatRunner` | Evaluates `condition_id` (or `branch_to_beat_id` always-true) and requests the target beat. |
| End | `EndBeat` | `EndBeatRunner` | Terminates the scene (`scene_finished`). |

---

## Runtime wiring

The minimal wiring (see `demo/demo_scene.gd` for a full example):

```gdscript
var director := SceneDirector.new()
add_child(director)

var bindings := SceneBindings.new()
add_child(bindings)

# Adapters live under the bindings; map authoring ids to node paths.
bindings.add_child(hero_adapter)
bindings.actor_nodes[&"hero"] = NodePath("Hero")

# Optional: hook dialogue lines / encounters / conditions.
var mech := SceneMechanicsRegistry.new()
bindings.add_child(mech)
bindings.mechanics_registry = mech
mech.register_effect(&"opening_line", _on_line)

director.plan = load("res://scenes/plans/my_plan.tres")
director.bindings = bindings
director.scene_finished.connect(_on_finished)
director.scene_failed.connect(_on_failed)
director.start_scene()
```

Actors implement `SceneActorAdapter`. For placeholders, `PlaceholderActorAdapter`
owns a `Marker3D` body and provides deadline-gated `move_to` / `look_at_target`
and a `request_action` that emits a configurable event sequence — enough for
prototyping cutscenes with zero game code.

---

## Validation

`ScenePlanValidator` (used by the dock and inspector) reports issues with stable
dotted codes under `scene_animator.validation.*`:

- **Errors** block playback: duplicate/missing beat or actor ids, dangling
  `next`/`failure`/branch targets, empty plan, no enabled beats, missing speaker,
  missing actor reference, and unregistered actions / camera modes / encounters /
  conditions.
- **Warnings** are tolerated: unreachable beats, missing `plan_id`, no declared
  actors, missing capability registry, focus-requiring camera without a focus
  target, unknown actor (authoring metadata only — runtime resolution comes from
  `SceneBindings`), and action tag mismatches.

A plan is `valid()` iff it has no errors.

---

## Tests and CI

- **`tests/parse_check.gd`** — loads every addon script in dependency order and
  every test resource; fails on any parse/load error or on a `.gd` missing from
  the manifest (full-tree coverage guard).
- **`tests/run_scene_animator_tests.gd`** — runs all suites in order and prints a
  single `SCENE_ANIMATOR_RESULT: {...}` JSON line, exiting 0/1/2.
  Suites: `test_runtime_execution`, `test_plugin_activation`, `test_validators`,
  `test_demo_execution`.
- **`tests/gate.sh`** — the canonical local gate: import -> parse check -> test
  runner, with `set -euo pipefail` and absolute paths (a relative `--log-file`
  crashes Godot 4.7.1 on Windows).

Run everything:

```bash
bash addons/scene_animator/tests/gate.sh
# override the engine binary with:
GODOT_BIN=/path/to/godot bash addons/scene_animator/tests/gate.sh
```

`.github/workflows/godot-tests.yml` runs the same gate on every push/PR to the
`scene-animator` branch: downloads the pinned Godot 4.7.1 headless binary
(SHA-256 verified), runs `gate.sh`, fails on any exit 1/2, checks the tree is
clean, and uploads the logs as an artifact.

---

## Repository layout

```
scene_animator/
  plugin.cfg / plugin.gd        # editor plugin (dock + inspector), idempotent
  data/                         # resources: ScenePlan, beats, bindings, capability registry
  runtime/                      # SceneDirector, SceneBindings, adapters, mechanics registry, runners
  editor/                       # dock, inspector, validator
  templates/starter_scene_plan.tres
  demo/                         # runnable demo scene + plan
  tests/                        # parse check, suite runner, gate.sh, fixtures, support fakes
```
