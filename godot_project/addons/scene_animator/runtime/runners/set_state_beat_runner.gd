@tool
class_name SetStateBeatRunner
extends BeatRunner

var _b: SetStateBeat


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as SetStateBeat


func start() -> void:
	var target := _bindings.get_node(_b.target_path)
	if target == null:
		failed.emit(&"missing_target", {"beat_id": _b.beat_id, "target_path": _b.target_path})
		return

	var mech := _bindings.mechanics_registry
	if mech != null and mech.set_state(target, _b.state_id):
		completed.emit()
		return

	if target.has_method(&"set_state"):
		target.set_state(_b.state_id)
		completed.emit()
		return

	failed.emit(&"no_state_setter", {
		"beat_id": _b.beat_id,
		"target_path": _b.target_path,
		"state_id": _b.state_id,
	})
