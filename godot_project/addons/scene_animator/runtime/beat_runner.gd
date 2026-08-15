@tool
class_name BeatRunner
extends Node

## Base class for every beat executor. The SceneDirector creates one runner per
## beat, connects completed/failed/branch_requested, starts it, and frees it
## when it signals.

signal completed
signal failed(reason: StringName, details: Dictionary)
signal branch_requested(target_beat_id: StringName)

## Stored by the base so generic helpers and the director can inspect state.
var _beat: SceneBeat
var _bindings: SceneBindings
var _registry: SceneCapabilityRegistry

# --------------------------------------------------------------------------- #
# Lifecycle (subclasses override)
# --------------------------------------------------------------------------- #

## Called by the director after instantiation. The base stores references so
## subclasses and shared helpers have access without re-fetching.
func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	_beat = beat
	_bindings = bindings
	_registry = registry


func _timeout_timer(wait_seconds: float) -> Timer:
	var t := Timer.new()
	t.one_shot = true
	t.wait_time = wait_seconds
	add_child(t)
	return t


## Called by the director right after setup(). The base treats the beat as
## instantly completable; subclasses override with real behavior.
func start() -> void:
	completed.emit()


func _ready() -> void:
	if not Engine.is_editor_hint():
		process_mode = Node.PROCESS_MODE_INHERIT


# --------------------------------------------------------------------------- #
# Factory
# --------------------------------------------------------------------------- #

const RUNNER_PATHS: Dictionary = {
	&"move_to":              "res://addons/scene_animator/runtime/runners/move_to_beat_runner.gd",
	&"look_at":              "res://addons/scene_animator/runtime/runners/look_at_beat_runner.gd",
	&"action":               "res://addons/scene_animator/runtime/runners/action_beat_runner.gd",
	&"wait":                 "res://addons/scene_animator/runtime/runners/wait_beat_runner.gd",
	&"wait_for_event":       "res://addons/scene_animator/runtime/runners/wait_for_event_beat_runner.gd",
	&"camera":               "res://addons/scene_animator/runtime/runners/camera_beat_runner.gd",
	&"dialogue":             "res://addons/scene_animator/runtime/runners/dialogue_beat_runner.gd",
	&"set_state":            "res://addons/scene_animator/runtime/runners/set_state_beat_runner.gd",
	&"spawn_encounter":      "res://addons/scene_animator/runtime/runners/spawn_encounter_beat_runner.gd",
	&"branch":               "res://addons/scene_animator/runtime/runners/branch_beat_runner.gd",
	&"end":                  "res://addons/scene_animator/runtime/runners/end_beat_runner.gd",
}

static var _script_cache: Dictionary = {}


static func _runner_script_for_type(beat_type: StringName) -> Script:
	if _script_cache.has(beat_type):
		return _script_cache[beat_type] as Script
	var path: String = RUNNER_PATHS.get(beat_type, "")
	if path == "":
		push_error("SceneAnimator: no runner registered for beat type '%s'" % beat_type)
		return null
	var script := load(path)
	if script == null:
		push_error("SceneAnimator: runner script failed to load: %s" % path)
		return null
	_script_cache[beat_type] = script
	return script


static func create(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> BeatRunner:
	if beat == null:
		return null
	var beat_type: StringName = beat.beat_type()
	var script := BeatRunner._runner_script_for_type(beat_type)
	if script == null:
		return null
	var runner: BeatRunner = script.new()
	runner.name = "BeatRunner_" + String(beat.beat_id)
	runner.setup(beat, bindings, registry)
	return runner
