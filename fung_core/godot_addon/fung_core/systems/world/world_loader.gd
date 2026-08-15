class_name WorldLoader
extends Node


func load_world(world_data: Dictionary, into: Node, tile_set: TileSet = null) -> WorldState:
	var world_state := WorldState.from_dict(world_data)
	if world_state == null:
		return null

	var builder := TileMapBuilder.new()
	var tile_map_layer := builder.build(world_state, tile_set)
	into.add_child(tile_map_layer)
	return world_state
