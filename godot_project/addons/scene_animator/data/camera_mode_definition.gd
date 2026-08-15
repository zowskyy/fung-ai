@tool
class_name CameraModeDefinition
extends Resource

## Contract describing one camera mode the animator may request.

@export var id: StringName
@export var display_name := ""
@export var is_dynamic := true
@export var default_blend_seconds := 0.25
@export var requires_focus_target := true
