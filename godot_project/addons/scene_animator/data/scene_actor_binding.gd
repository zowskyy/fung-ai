@tool
class_name SceneActorBinding
extends Resource

## Maps a stable authoring ID (used in beats) to a node path in the edited scene
## plus the semantic tags that describe the actor to the capability registry.

@export var actor_id: StringName
@export var display_name := ""
@export var actor_path: NodePath
@export var actor_tags: Array[StringName] = []
@export var required := true


func is_bound() -> bool:
	return not actor_path.is_empty()
