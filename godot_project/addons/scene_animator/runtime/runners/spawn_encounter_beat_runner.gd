@tool
class_name SpawnEncounterBeatRunner
extends BeatRunner

var _b: SpawnEncounterBeat
var _timeout: Timer
var _done := false


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as SpawnEncounterBeat


func start() -> void:
	var mech := _bindings.mechanics_registry
	if mech == null or not mech.has_encounter(_b.encounter_id):
		failed.emit(&"encounter_not_registered", {
			"beat_id": _b.beat_id,
			"encounter_id": _b.encounter_id,
		})
		return

	var spawner := mech.spawn_encounter(_b.encounter_id, _b.spawn_markers)
	if spawner == null:
		failed.emit(&"encounter_spawn_failed", {
			"beat_id": _b.beat_id,
			"encounter_id": _b.encounter_id,
		})
		return

	if _b.wait_until_cleared:
		mech.encounter_cleared.connect(_on_cleared)
		_timeout = _timeout_timer(_b.timeout_seconds)
		_timeout.timeout.connect(_on_timeout)
		_timeout.start()
	else:
		completed.emit()


func _on_cleared(encounter_id: StringName) -> void:
	if _done:
		return
	if encounter_id == _b.encounter_id:
		_done = true
		completed.emit()


func _on_timeout() -> void:
	if _done:
		return
	_done = true
	failed.emit(&"encounter_timeout", {
		"beat_id": _b.beat_id,
		"encounter_id": _b.encounter_id,
		"timeout_seconds": _b.timeout_seconds,
	})
