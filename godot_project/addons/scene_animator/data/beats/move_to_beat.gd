@tool
class_name MoveToBeat
extends SceneBeat

@export_category("Move To")
@export var actor_id: StringName
@export var target_path: NodePath
@export var arrival_radius := 0.4
@export_enum("walk", "run", "custom")
var locomotion_mode: String = "walk"
@export var timeout_seconds := 8.0


func beat_type() -> StringName:
	return &"move_to"
