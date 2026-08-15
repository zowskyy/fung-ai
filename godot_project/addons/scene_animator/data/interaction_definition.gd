@tool
class_name InteractionDefinition
extends Resource

## Contract describing a targetable interaction (used by look-at / action beats
## to resolve which targets are valid for a given mechanic).

@export var id: StringName
@export var display_name := ""
@export var required_target_tags: Array[StringName] = []
@export var interaction_radius := 2.0
