@tool
class_name ActionBeatRunner
extends BeatRunner

var _b: ActionBeat
var _timeout: Timer
var _done := false
var _action_def: ActionDefinition


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as ActionBeat


func start() -> void:
	var actor := _bindings.get_actor(_b.actor_id)
	var target := _bindings.get_node(_b.target_path) as Node3D

	if actor == null:
		failed.emit(&"missing_actor", {"beat_id": _b.beat_id, "actor_id": _b.actor_id})
		return
	if target == null:
		failed.emit(&"missing_target", {"beat_id": _b.beat_id, "target_path": _b.target_path})
		return

	_action_def = _registry.find_action(_b.action_id) if _registry != null else null

	if _b.wait_for_completion:
		actor.action_completed.connect(_on_action_completed, CONNECT_ONE_SHOT)
		actor.action_failed.connect(_on_action_failed, CONNECT_ONE_SHOT)
	else:
		call_deferred("_finish_if_not_done")

	actor.request_action(
		_b.action_id,
		target,
		{
			"scene_beat_id": _b.beat_id,
			"completion_event": _b.completion_event,
			"action_definition": _action_def,
		}
	)

	if _b.timeout_seconds > 0.0:
		_timeout = _timeout_timer(_b.timeout_seconds)
		_timeout.timeout.connect(_on_timeout)
		_timeout.start()


func _on_action_completed(_action_id: StringName) -> void:
	_finish_if_not_done()


func _on_action_failed(_action_id: StringName, reason: StringName) -> void:
	if _done:
		return
	_done = true
	failed.emit(&"actor_action_failed", {
		"beat_id": _b.beat_id,
		"actor_id": _b.actor_id,
		"action_id": _b.action_id,
		"adapter_reason": reason,
	})


func _on_timeout() -> void:
	if _done:
		return
	_done = true
	failed.emit(&"action_timeout", {
		"beat_id": _b.beat_id,
		"actor_id": _b.actor_id,
		"action_id": _b.action_id,
		"timeout_seconds": _b.timeout_seconds,
	})


func _finish_if_not_done() -> void:
	if _done:
		return
	_done = true
	completed.emit()
