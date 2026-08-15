@tool
class_name MoveToBeatRunner
extends BeatRunner

var _b: MoveToBeat
var _timeout: Timer
var _done := false


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as MoveToBeat


func start() -> void:
	var actor := _bindings.get_actor(_b.actor_id)
	var target := _bindings.get_node(_b.target_path) as Node3D
	if actor == null:
		failed.emit(&"missing_actor", {"beat_id": _b.beat_id, "actor_id": _b.actor_id})
		return
	if target == null:
		failed.emit(&"missing_target", {"beat_id": _b.beat_id, "target_path": _b.target_path})
		return

	actor.destination_reached.connect(_on_reached, CONNECT_ONE_SHOT)
	actor.action_failed.connect(_on_failed, CONNECT_ONE_SHOT)
	actor.move_to(target, _b.arrival_radius, StringName(_b.locomotion_mode))

	_timeout = _timeout_timer(_b.timeout_seconds)
	_timeout.timeout.connect(_on_timeout)
	_timeout.start()


func _on_reached(_target: Node3D) -> void:
	if _done:
		return
	_done = true
	completed.emit()


func _on_failed(_actor: StringName, reason: StringName) -> void:
	if _done:
		return
	_done = true
	failed.emit(reason, {"beat_id": _b.beat_id, "actor_id": _b.actor_id})


func _on_timeout() -> void:
	if _done:
		return
	_done = true
	failed.emit(&"move_timeout", {"beat_id": _b.beat_id, "actor_id": _b.actor_id, "timeout_seconds": _b.timeout_seconds})
