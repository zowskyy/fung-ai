@tool
class_name WaitBeat
extends SceneBeat

@export_category("Wait")
@export var duration_seconds := 1.0


func beat_type() -> StringName:
	return &"wait"
