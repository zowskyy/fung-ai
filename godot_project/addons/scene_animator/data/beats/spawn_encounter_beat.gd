@tool
class_name SpawnEncounterBeat
extends SceneBeat

@export_category("Encounter")
@export var encounter_id: StringName
@export var spawn_markers: Array[NodePath] = []
@export var wait_until_cleared := false
@export var timeout_seconds := 60.0


func beat_type() -> StringName:
	return &"spawn_encounter"
