@tool
class_name SceneDirector
extends Node

## Deterministic sequencer. Drives a ScenePlan through BeatRunners using
## SceneBindings + SceneCapabilityRegistry. Emits scene_started / scene_finished /
## scene_failed. Beats chain via next_beat_id; failures chain via failure_beat_id;
## BranchBeat overrides the next target via branch_requested. A plan reaches
## exactly one terminal state.

signal scene_started
signal scene_finished
signal scene_failed(reason: StringName, details: Dictionary)

@export var plan: ScenePlan
@export var bindings: SceneBindings
@export var registry: SceneCapabilityRegistry

var _current_beat: SceneBeat
var _active_runner: BeatRunner
var _started := false
var _terminal := false


func _init() -> void:
	if not Engine.is_editor_hint():
		process_mode = Node.PROCESS_MODE_INHERIT


func start_scene() -> void:
	if _terminal or _started:
		return
	if plan == null:
		_fail(&"missing_plan", {})
		return
	if plan.beats.is_empty():
		_fail(&"empty_plan", {"plan_id": plan.plan_id if plan != null else &""})
		return
	if bindings == null:
		_fail(&"missing_bindings", {"plan_id": plan.plan_id})
		return

	_started = true
	scene_started.emit()
	_run_beat(plan.first_enabled_beat())


func stop_scene() -> void:
	if _active_runner != null:
		if _active_runner.is_inside_tree():
			_active_runner.queue_free()
		_active_runner = null
	_started = false


func _run_beat(beat: SceneBeat) -> void:
	if _terminal:
		return
	if beat == null:
		_finish_scene()
		return

	_current_beat = beat
	_active_runner = BeatRunner.create(beat, bindings, registry)

	if _active_runner == null:
		_fail(&"unsupported_beat", {
			"beat_id": beat.beat_id if beat != null else &"",
			"beat_type": beat.beat_type() if beat != null else &"",
		})
		return

	add_child(_active_runner)
	_active_runner.completed.connect(_on_beat_completed)
	_active_runner.failed.connect(_on_beat_failed)
	_active_runner.branch_requested.connect(_on_branch_requested)
	_active_runner.start()


func _on_beat_completed() -> void:
	if _terminal:
		return
	var next := _find_beat(_current_beat.next_beat_id)
	_disconnect_current()
	_run_beat(next)


func _on_beat_failed(reason: StringName, details: Dictionary) -> void:
	if _terminal:
		return
	var fallback := _find_beat(_current_beat.failure_beat_id)
	_disconnect_current()
	if fallback != null:
		_run_beat(fallback)
	else:
		_fail(reason, details)


func _on_branch_requested(target_beat_id: StringName) -> void:
	if _terminal:
		return
	_disconnect_current()
	var target := plan.beat_by_id(target_beat_id)
	_run_beat(target)


func _finish_scene() -> void:
	if _terminal:
		return
	_terminal = true
	_started = false
	_active_runner = null
	_current_beat = null
	scene_finished.emit()


func _fail(reason: StringName, details: Dictionary) -> void:
	if _terminal:
		return
	_terminal = true
	_started = false
	_disconnect_current()
	_active_runner = null
	_current_beat = null
	var merged: Dictionary = details.duplicate(true)
	merged["reason"] = reason
	if plan != null:
		merged["plan_id"] = plan.plan_id
	scene_failed.emit(reason, merged)


func _disconnect_current() -> void:
	if _active_runner == null:
		return
	if _active_runner.is_connected(&"completed", Callable(_on_beat_completed)):
		_active_runner.disconnect(&"completed", Callable(_on_beat_completed))
	if _active_runner.is_connected(&"failed", Callable(_on_beat_failed)):
		_active_runner.disconnect(&"failed", Callable(_on_beat_failed))
	if _active_runner.is_connected(&"branch_requested", Callable(_on_branch_requested)):
		_active_runner.disconnect(&"branch_requested", Callable(_on_branch_requested))


func _find_beat(id: StringName) -> SceneBeat:
	if id == &"" or plan == null:
		return null
	return plan.beat_by_id(id)
