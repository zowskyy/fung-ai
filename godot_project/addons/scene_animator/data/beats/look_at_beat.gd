@tool
class_name LookAtBeat
extends SceneBeat

@export_category("Look At")
@export var actor_id: StringName
@export var target_path: NodePath
@export var max_turn_seconds := 0.5


func beat_type() -> StringName:
	return &"look_at"
