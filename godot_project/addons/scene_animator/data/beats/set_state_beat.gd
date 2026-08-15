@tool
class_name SetStateBeat
extends SceneBeat

## Sets a named state on a target actor/node (e.g. "displaced", "open"). The
## state-setter is resolved through the mechanics registry.

@export_category("Set State")
@export var target_path: NodePath
@export var state_id: StringName
@export var timeout_seconds := 3.0


func beat_type() -> StringName:
	return &"set_state"
