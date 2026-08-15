@tool
class_name WaitForEventBeat
extends SceneBeat

@export_category("Event")
@export var source_actor_id: StringName
@export var event_name: StringName
@export var timeout_seconds := 4.0


func beat_type() -> StringName:
	return &"wait_for_event"
