@tool
class_name ActionBeat
extends SceneBeat

@export_category("Action")
@export var actor_id: StringName
@export var action_id: StringName
@export var target_path: NodePath
@export var wait_for_completion := true
@export var completion_event: StringName = &"action_complete"
@export var timeout_seconds := 5.0


func beat_type() -> StringName:
	return &"action"
