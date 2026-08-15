@tool
class_name BranchBeat
extends SceneBeat

## Unconditional or condition-gated branch. On start it resolves the condition
## (if any) through the registry; the runner emits branch_requested to the
## director with the resolved target beat, bypassing next_beat_id.

@export_category("Branch")
@export var condition_id: StringName
@export var target_beat_id: StringName
@export var else_target_beat_id: StringName


func beat_type() -> StringName:
	return &"branch"
