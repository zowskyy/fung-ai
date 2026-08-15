class_name SpawnService
extends RefCounted


func get_spawn_position(world_state: WorldState, spawn_id: String) -> Vector2i:
	var spawn := world_state.get_spawn(spawn_id)
	if spawn.is_empty():
		push_error("SpawnService: no spawn found with id '%s'" % spawn_id)
		# Vector2i(-1, -1) is the documented "not found" sentinel; it could
		# otherwise look like a valid coordinate.
		return Vector2i(-1, -1)
	return Vector2i(spawn["x"], spawn["y"])
