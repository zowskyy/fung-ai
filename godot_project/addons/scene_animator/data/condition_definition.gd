@tool
class_name ConditionDefinition
extends Resource

## Contract describing a named, registry-validated condition used by branch beats.

@export var id: StringName
@export var display_name := ""
@export var evaluator_script: String = ""
