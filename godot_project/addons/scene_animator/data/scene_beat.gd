@tool
class_name SceneBeat
extends Resource

## Base type for every authored beat. Concrete beats extend this and add their
## configuration. The linear flow fields live here so every beat can chain.

@export var beat_id: StringName
@export var display_name := ""
@export var enabled := true

@export_category("Flow")
@export var next_beat_id: StringName
@export var failure_beat_id: StringName

@export_category("Diagnostics")
@export_multiline var note := ""

## The concrete beat type, used by the runner factory and for validation.
func beat_type() -> StringName:
	return &"base"
