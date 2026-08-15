@tool
class_name BranchBeatRunner
extends BeatRunner

var _b: BranchBeat
var _done := false


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as BranchBeat


func start() -> void:
	if _done:
		return
	_done = true

	var target := _b.target_beat_id
	if _b.condition_id != &"":
		var mech := _bindings.mechanics_registry
		if mech != null and mech.has_condition(_b.condition_id):
			if not mech.evaluate_condition(_b.condition_id):
				target = _b.else_target_beat_id
		else:
			target = _b.else_target_beat_id

	if target != &"":
		branch_requested.emit(target)
	else:
		completed.emit()
