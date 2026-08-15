class_name WorldState
extends RefCounted

var id: String
var seed: int
var width: int
var height: int
var tiles: PackedInt32Array
var spawns: Array


# This is a boundary guard only, not full JSON-Schema validation - that
# responsibility lives in the Python tooling before data ever reaches Godot.
static func from_dict(data: Dictionary) -> WorldState:
	var required_keys := ["version", "id", "width", "height", "tiles", "spawns"]
	for key in required_keys:
		if not data.has(key):
			push_error("WorldState.from_dict: missing required key '%s'" % key)
			return null

	var w: int = data["width"]
	var h: int = data["height"]
	var tiles_raw: Array = data["tiles"]
	if tiles_raw.size() != w * h:
		push_error("WorldState.from_dict: tiles.size() (%d) does not equal width*height (%d)" % [tiles_raw.size(), w * h])
		return null

	var spawns_raw: Array = data["spawns"]
	if spawns_raw.is_empty():
		push_error("WorldState.from_dict: spawns must not be empty")
		return null

	var state := WorldState.new()
	state.id = data["id"]
	state.seed = data.get("seed", 0)
	state.width = w
	state.height = h
	var packed_tiles := PackedInt32Array()
	packed_tiles.resize(tiles_raw.size())
	for i in tiles_raw.size():
		packed_tiles[i] = tiles_raw[i]
	state.tiles = packed_tiles
	state.spawns = spawns_raw
	return state


func is_in_bounds(x: int, y: int) -> bool:
	return x >= 0 and x < width and y >= 0 and y < height


func is_wall(x: int, y: int) -> bool:
	if not is_in_bounds(x, y):
		return true
	return tiles[y * width + x] == 1


func get_spawn(spawn_id: String) -> Dictionary:
	for spawn in spawns:
		if spawn.get("id", "") == spawn_id:
			return spawn
	return {}
