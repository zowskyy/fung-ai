class_name ComponentFactory
extends RefCounted


func create_entity(entity_data: Dictionary, archetype_db: ArchetypeDatabase, tile_size: float = 32.0) -> Node2D:
	var defaults: Dictionary = archetype_db.get_archetype(entity_data.get("archetype", ""))
	var effective: Dictionary = defaults.duplicate()
	for key in entity_data:
		effective[key] = entity_data[key]

	var node := Node2D.new()
	node.name = entity_data.id
	node.position = Vector2(entity_data.position.x, entity_data.position.y) * tile_size

	node.set_meta("health", effective.get("health", 0))
	node.set_meta("animation_id", effective.get("animation_id", ""))
	node.set_meta("tags", effective.get("tags", []))
	node.set_meta("archetype", entity_data.get("archetype", ""))
	node.set_meta("entity_id", entity_data.id)
	return node
