class_name EntityRegistry
extends RefCounted

var _entities: Dictionary = {}


func register(entity_id: String, node: Node) -> void:
	_entities[entity_id] = node


func unregister(entity_id: String) -> void:
	_entities.erase(entity_id)


func get_entity(entity_id: String) -> Node:
	return _entities.get(entity_id, null)


func get_by_tag(tag: String) -> Array:
	var result: Array = []
	for entity_id in _entities:
		var node: Node = _entities[entity_id]
		var tags: Array = node.get_meta("tags", [])
		if tags.has(tag):
			result.append(node)
	return result
