@tool
class_name CameraBeat
extends SceneBeat

@export_category("Camera")
@export var camera_mode_id: StringName
@export var focus_target_path: NodePath
@export var blend_seconds := 0.25


func beat_type() -> StringName:
	return &"camera"
