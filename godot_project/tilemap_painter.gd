# tilemap_painter.gd — Efficient TileMapLayer renderer for CA-generated caves.
#
# Replaces the O(n) ColorRect approach in CaveRenderer.gd which creates one
# Node per tile (2 500 nodes for a 50x50 cave).  TileMapLayer.set_cell() keeps
# the entire grid in a single draw call, so a 50x50 cave goes from ~2 500
# CanvasItem draw calls to 1.
#
# Usage:
#   var painter = TileMapPainter.new()
#   painter.paint_grid(my_layer, bridge.generate()["grid"])
#   # — or —
#   painter.paint_grid_from_json(my_layer, "res://cave.json")

extends RefCounted
class_name TileMapPainter

# Atlas source indices within the TileSet attached to the TileMapLayer.
# The caller is responsible for setting up a TileSet with at least one
# AtlasTileSource whose tiles match these coordinates.
const WALL_TILE_ID  := 0   # atlas coords (0,0) — dark / solid
const FLOOR_TILE_ID := 1   # atlas coords (1,0) — light / open

const WALL_ATLAS_COORDS  := Vector2i(0, 0)
const FLOOR_ATLAS_COORDS := Vector2i(1, 0)


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #

## Paint a raw CA grid onto *layer*.
##
## grid  — Array[Array[float]], row-major, 0.0 = wall, 1.0 = floor.
##         (The exact output of CaBridge.generate()["grid"].)
## source_id — TileSet source ID to use (default 0).
##
## If the layer has no TileSet, a warning is printed and the call is a no-op.
func paint_grid(layer: TileMapLayer, grid: Array, source_id: int = 0) -> void:
	if not _tileset_ok(layer):
		return

	layer.clear()

	for row_idx in range(grid.size()):
		var row: Array = grid[row_idx]
		for col_idx in range(row.size()):
			var cell_val := float(row[col_idx])
			if cell_val >= 0.5:
				layer.set_cell(Vector2i(col_idx, row_idx), source_id, FLOOR_ATLAS_COORDS)
			else:
				layer.set_cell(Vector2i(col_idx, row_idx), source_id, WALL_ATLAS_COORDS)


## Remove all tiles from *layer*.
func clear_grid(layer: TileMapLayer) -> void:
	layer.clear()


## Return the number of cells that currently have a tile set on *layer*.
func get_tile_count(layer: TileMapLayer) -> int:
	return layer.get_used_cells().size()


## Load a cave JSON file (godot_scene.json format) and paint it onto *layer*.
##
## The JSON must have a top-level "tilemap" Array whose elements each contain:
##   "coords": [row, col]  (grid cell index, not pixel position)
##   "type": "wall" | "floor"
##
## Returns true on success, false on any failure.
func paint_grid_from_json(layer: TileMapLayer, json_path: String, source_id: int = 0) -> bool:
	if not FileAccess.file_exists(json_path):
		push_error("TileMapPainter: file does not exist: %s" % json_path)
		return false

	var f := FileAccess.open(json_path, FileAccess.READ)
	if f == null:
		push_error("TileMapPainter: could not open file: %s" % json_path)
		return false

	var text := f.get_as_text()
	f.close()

	var parsed = JSON.parse_string(text)
	if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
		push_error("TileMapPainter: JSON parse failed for %s" % json_path)
		return false

	var data: Dictionary = parsed
	if not data.has("tilemap"):
		push_error("TileMapPainter: JSON has no 'tilemap' key: %s" % json_path)
		return false

	var tilemap: Array = data["tilemap"]
	if tilemap.is_empty():
		push_warning("TileMapPainter: 'tilemap' array is empty in %s" % json_path)
		return true   # technically not an error; just nothing to paint

	if not _tileset_ok(layer):
		return false

	layer.clear()

	for tile in tilemap:
		if not (tile.has("coords") and tile.has("type")):
			push_warning("TileMapPainter: tile missing 'coords' or 'type', skipping: %s" % str(tile))
			continue

		var coords: Array = tile["coords"]   # [row, col]
		if coords.size() < 2:
			push_warning("TileMapPainter: 'coords' has fewer than 2 elements, skipping: %s" % str(tile))
			continue

		var cell := Vector2i(int(coords[1]), int(coords[0]))   # col → x, row → y

		if tile["type"] == "floor":
			layer.set_cell(cell, source_id, FLOOR_ATLAS_COORDS)
		else:
			layer.set_cell(cell, source_id, WALL_ATLAS_COORDS)

	return true


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

## Returns true when *layer* has a TileSet configured.
## Prints a warning (not an error) when the TileSet is absent, because callers
## may be testing the bridge without a fully configured scene.
func _tileset_ok(layer: TileMapLayer) -> bool:
	if layer == null:
		push_error("TileMapPainter: layer is null")
		return false
	if layer.tile_set == null:
		push_warning("TileMapPainter: TileMapLayer has no TileSet — paint skipped. "
				+ "Attach a TileSet with at least one AtlasTileSource first.")
		return false
	return true
