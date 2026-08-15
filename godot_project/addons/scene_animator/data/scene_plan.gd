@tool
class_name ScenePlan
extends Resource

## Authoring root. A plan is a reusable, shareable resource describing a
## deterministic scene sequence. Save under res://scenes/plans/.

@export var plan_id: StringName
@export var display_name := ""
@export_multiline var description := ""

@export_category("Dependencies")
@export var capabilities: SceneCapabilityRegistry

@export_category("Content")
@export var actors: Array[SceneActorBinding] = []
@export var beats: Array[SceneBeat] = []

@export_category("Generation")
@export var schema_version := 1
@export var create_generated_root := true


func beat_by_id(id: StringName) -> SceneBeat:
	for b in beats:
		if b.beat_id == id:
			return b
	return null


func find_actor(id: StringName) -> SceneActorBinding:
	for a in actors:
		if a.actor_id == id:
			return a
	return null


func first_enabled_beat() -> SceneBeat:
	for b in beats:
		if b.enabled:
			return b
	return null


func beat_ids() -> Array[StringName]:
	var out: Array[StringName] = []
	for b in beats:
		out.append(b.beat_id)
	return out
