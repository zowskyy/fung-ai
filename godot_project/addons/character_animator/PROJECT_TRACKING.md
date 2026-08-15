# Project Tracking — 2D Character Animator addon

## Purpose

A Godot 4.x addon that authors and drives 2D character animation through three
interchangeable approaches (sprite-frame clips, an AnimationTree state machine
generated from those clips, and Skeleton2D/Bone2D bone animation). The plugin
builds and drives Godot's own animation systems rather than re-implementing
them, so generated graphs are standard, editable Godot resources.

## Layout

| Path | Purpose | Status |
| --- | --- | --- |
| `godot_project/addons/character_animator/plugin.cfg` | Plugin manifest | complete |
| `godot_project/addons/character_animator/plugin.gd` | EditorPlugin: dock, custom types, inspectors | complete |
| `runtime/animation_clip.gd` | `AnimationClip` resource (frame regions) | complete |
| `runtime/character_animator.gd` | Sprite2D frame-clip player | complete |
| `runtime/character_animation_profile.gd` | Profile resource (clip roles, thresholds) | complete |
| `runtime/character_animation_driver.gd` | Runtime AnimationTree bridge | complete |
| `runtime/character_animation_state.gd` | Serializable state/transition data | complete |
| `runtime/animation_event_receiver.gd` | Event API + vocabulary for clips | complete |
| `runtime/bone_def.gd` | Bone definition | complete |
| `runtime/bone_key.gd` | Bone keyframe | complete |
| `runtime/bone_track.gd` | Per-bone key track | complete |
| `runtime/bone_clip.gd` | Bone animation clip | complete |
| `runtime/character_rig.gd` | Rig (bone list, hierarchy) | complete |
| `runtime/character_skeleton.gd` | Skeleton2D/Bone2D builder | complete |
| `runtime/skeleton_animator.gd` | BoneClip player | complete |
| `runtime/sprite_sheet_factory.gd` | Runtime placeholder art | complete |
| `editor/character_scene_scanner.gd` | Scans scene for animation nodes | complete |
| `editor/animation_graph_builder.gd` | Clips -> AnimationPlayer + state machine | complete |
| `editor/animation_validator.gd` | Setup validation | complete |
| `editor/validation_issue.gd` | Structured validation result | complete |
| `editor/undo_service.gd` | Undo wrapper around editor UndoRedo | complete |
| `editor/texture_region_editor.gd` | Sprite-sheet region picker | complete |
| `editor/clip_editor_tab.gd` | Clips tab UI | complete |
| `editor/rig_editor_tab.gd` | Rig tab UI | complete |
| `editor/setup_tab.gd` | Setup tab UI | complete |
| `editor/inspectors/character_animation_profile_inspector.gd` | Profile inspector | complete |
| `ui/character_animator_dock.gd` | Dock controller | complete |
| `ui/character_animator_dock.tscn` | Dock scene | complete |
| `demo/demo.tscn` + `demo/demo.gd` | Runtime demo (player + skeleton NPC) | complete |
| `demo/player.gd` | Reference CharacterBody2D controller | complete |
| `tests/run_tests.gd` | Headless test runner | complete |
| `.github/workflows/ci.yml` (godot-plugin job) | CI: import + run tests | complete |

## Open dependencies

None. All code referenced by generated graphs and the dock exists and is wired.

## Known gaps

- The Rig tab targets `CharacterSkeleton` nodes that are `Node2D` with the
  `character_skeleton.gd` script attached (the script registers `class_name
  CharacterSkeleton`). A native `CharacterSkeleton` node type would need a
  `script_class`-based `add_custom_type` or an `@icon` + typed script; the
  current approach keeps the demo and tests portable.
- `AnimationValidator` reports issues but the Setup tab does not yet expose
  one-click `fix_id` actions for every `ValidationIssue` (INFO/WARNING/ERROR
  display is wired; automated fixes are not).
- The generated state machine is a fixed side-scroller locomotion graph
  (idle/walk/run/jump/fall/land/crouch). Custom graphs are intentionally left to
  Godot's AnimationTree editor.
- `Skeleton2D` prints engine-internal `affine_invert det == 0` noise when
  runtime-built bone hierarchies are freed (headless only); it is non-fatal and
  does not affect the test result or CI exit code.
