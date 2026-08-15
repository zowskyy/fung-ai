@tool
class_name SceneBindings
extends Node

## Runtime resolver mapping authoring IDs/NodePaths to actual scene nodes.
## Lives under the generated root so it can own its child bindings too.

signal actor_resolved(actor_id: StringName, adapter: SceneActorAdapter)
signal binding_missing(actor_id: StringName)

@export var actor_nodes: Dictionary[StringName, NodePath] = {}
@export var named_nodes: Dictionary[StringName, NodePath] = {}

## Optional mechanics registry used by encounter / state-setter / effect beats.
@export var mechanics_registry: SceneMechanicsRegistry
## Optional camera adapter provider for camera beats.
@export var camera_adapter: SceneCameraAdapter


func get_actor(actor_id: StringName) -> SceneActorAdapter:
	if not actor_nodes.has(actor_id):
		binding_missing.emit(actor_id)
		return null
	var path: NodePath = actor_nodes[actor_id]
	if path.is_empty():
		binding_missing.emit(actor_id)
		return null
	var node := get_node_or_null(path)
	if node == null:
		binding_missing.emit(actor_id)
		return null
	var adapter := node as SceneActorAdapter
	if adapter == null:
		binding_missing.emit(actor_id)
		return null
	actor_resolved.emit(actor_id, adapter)
	return adapter


func get_node(actor_path: NodePath) -> Node:
	return get_node_or_null(actor_path)


func get_named_node(id: StringName) -> Node:
	if not named_nodes.has(id):
		return null
	var path: NodePath = named_nodes[id]
	if path.is_empty():
		return null
	return get_node_or_null(path)


func has_actor(actor_id: StringName) -> bool:
	return actor_nodes.has(actor_id) and not actor_nodes[actor_id].is_empty()


func has_named_node(id: StringName) -> bool:
	return named_nodes.has(id) and not named_nodes[id].is_empty()
