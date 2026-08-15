class_name EncounterSpawner
extends Node

signal encounter_triggered(encounter_id: String, narrative_id: String)


func spawn(encounter_data: Dictionary, entity_data: Dictionary, world_state: WorldState, entity_registry: EntityRegistry, spawn_service: SpawnService, archetype_db: ArchetypeDatabase, tile_size: float = 32.0) -> Node2D:
	var spawn_pos := spawn_service.get_spawn_position(world_state, encounter_data.spawn_point)

	var positioned_entity_data: Dictionary = entity_data.duplicate()
	positioned_entity_data.position = {"x": spawn_pos.x, "y": spawn_pos.y}

	var factory := ComponentFactory.new()
	var node := factory.create_entity(positioned_entity_data, archetype_db, tile_size)

	add_child(node)
	entity_registry.register(entity_data.id, node)

	# No proximity/trigger-volume detection in this vertical slice - spawning
	# a boss encounter immediately fires its story beat.
	encounter_triggered.emit(encounter_data.id, encounter_data.get("narrative_id", ""))
	return node
