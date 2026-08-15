@tool
class_name EncounterDefinition
extends Resource

## Contract describing one spawnable encounter (enemies, loot, triggers, ...).

@export var id: StringName
@export var display_name := ""
@export var spawn_marker_ids: Array[StringName] = []
@export var requires_clear_condition := false
