@tool
class_name SceneCapabilityRegistry
extends Resource

## Validates that a plan only requests actions / cameras / encounters /
## conditions that exist in the game. A plan references one registry; the same
## registry can be shared across many plans or swapped per project.

@export var actions: Array[ActionDefinition] = []
@export var interactions: Array[InteractionDefinition] = []
@export var camera_modes: Array[CameraModeDefinition] = []
@export var encounters: Array[EncounterDefinition] = []
@export var conditions: Array[ConditionDefinition] = []


func find_action(id: StringName) -> ActionDefinition:
	for a in actions:
		if a.id == id:
			return a
	return null


func find_interaction(id: StringName) -> InteractionDefinition:
	for i in interactions:
		if i.id == id:
			return i
	return null


func find_camera_mode(id: StringName) -> CameraModeDefinition:
	for c in camera_modes:
		if c.id == id:
			return c
	return null


func find_encounter(id: StringName) -> EncounterDefinition:
	for e in encounters:
		if e.id == id:
			return e
	return null


func find_condition(id: StringName) -> ConditionDefinition:
	for c in conditions:
		if c.id == id:
			return c
	return null
