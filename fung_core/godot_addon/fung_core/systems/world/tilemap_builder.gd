class_name TileMapBuilder
extends RefCounted


func build(world_state: WorldState, tile_set: TileSet = null) -> TileMapLayer:
	var layer := TileMapLayer.new()
	layer.set_meta("fung_tiles", world_state.tiles)
	layer.set_meta("fung_width", world_state.width)
	layer.set_meta("fung_height", world_state.height)

	if tile_set == null:
		return layer

	layer.tile_set = tile_set
	for y in world_state.height:
		for x in world_state.width:
			if world_state.is_wall(x, y):
				layer.set_cell(Vector2i(x, y), 0, Vector2i(0, 0))
	return layer
