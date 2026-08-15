@tool
class_name ActionDefinition
extends Resource

## Contract describing one animation/gameplay action an actor can perform.

@export var id: StringName
@export var display_name := ""

@export_category("Requirements")
@export var required_actor_tags: Array[StringName] = []
@export var required_target_tags: Array[StringName] = []

@export_category("Animation Contract")
@export var animation_state: StringName
@export_enum("none", "in_place", "planar_root_motion", "full_root_motion")
var motion_mode: String = "none"

@export_category("Events")
@export var completion_event: StringName = &"action_complete"
@export var required_events: Array[StringName] = []


func matches_tags(actor_tags: Array[StringName], target_tags: Array[StringName]) -> bool:
	for tag in required_actor_tags:
		if not (tag in actor_tags):
			return false
	for tag in required_target_tags:
		if not (tag in target_tags):
			return false
	return true
