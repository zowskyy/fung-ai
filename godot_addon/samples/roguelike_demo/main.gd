extends Node2D

# Fung Godot Toolkit - roguelike_demo sample project.
#
# Loads a real, pre-generated candidate payload (produced by actually
# running `python -m bridge.fung_bridge` against the recipe
# "compact_roguelike_rooms" - see data/README.md) and builds a playable
# level from it at runtime: decodes the rle-v1 grid into a TileMapLayer,
# places a spawn/exit marker pair, and spawns a simple top-down player
# controller (player.gd) at the PlayerSpawn position.
#
# This intentionally mirrors what fung_export_service.gd's
# _build_scene()/_decode_grid() do when exporting a candidate to a .tscn
# from inside the editor, just done at runtime from bundled JSON instead of
# via a pre-exported hand-authored scene (a TileMapLayer scene file with
# thousands of individual tile-cell entries would be far too easy to get
# subtly wrong by hand, with no Godot binary available to check it).
#
# UNVERIFIED: authored with no Godot binary available in this environment.
# Not run or tested by a real Godot engine - see repo root commit message
# and this project's README.md.

const TILE_SIZE := 16
const DATA_DIR := "res://data"
const RESULT_PATH := "res://data/result.json"

const PlayerScript := preload("res://player.gd")
const TilesetBuilder := preload("res://tileset_builder.gd")


func _ready() -> void:
	var result: Dictionary = _read_json(RESULT_PATH)
	if result.is_empty():
		push_error("Failed to load result.json - is data/result.json present?")
		return

	var candidates: Array = result.get("candidates", [])
	if candidates.is_empty():
		push_error("result.json has no candidates")
		return

	var candidate: Dictionary = candidates[0]
	var payload_path: String = DATA_DIR.path_join(candidate.get("payload_path", ""))
	var payload: Dictionary = _read_json(payload_path)
	if payload.is_empty():
		push_error("Failed to load candidate payload: %s" % payload_path)
		return

	_build_terrain(payload)
	_build_exit_marker(payload)
	_spawn_player(payload)
	_build_debug_label(result, payload)


func _build_terrain(payload: Dictionary) -> void:
	var grid_size: Array = payload.get("grid_size", [48, 48])
	var width: int = int(grid_size[0])
	var height: int = int(grid_size[1])
	var grid: PackedByteArray = _decode_grid_rle(payload.get("grid", ""), width, height)
	if grid.is_empty():
		push_error("Failed to decode candidate grid")
		return

	var tilemap: TileMapLayer = TileMapLayer.new()
	tilemap.name = "Terrain"
	tilemap.tile_set = TilesetBuilder.new().build()

	for y in range(height):
		for x in range(width):
			var cell_idx: int = y * width + x
			var is_wall: int = grid[cell_idx]
			# Wall=1 -> tile_id 1, Floor=0 -> tile_id 0 (matches
			# fung_export_service.gd's _build_scene() exactly).
			tilemap.set_cell(Vector2i(x, y), 0, Vector2i(is_wall, 0))

	add_child(tilemap)


func _build_exit_marker(payload: Dictionary) -> void:
	var exit_cell: Array = payload.get("exit_cell", [0, 0])
	var exit_marker: Marker2D = Marker2D.new()
	exit_marker.name = "Exit"
	exit_marker.position = Vector2(exit_cell[0] * TILE_SIZE, exit_cell[1] * TILE_SIZE)
	add_child(exit_marker)

	var visual: ColorRect = ColorRect.new()
	visual.size = Vector2(TILE_SIZE, TILE_SIZE)
	visual.position = Vector2(-TILE_SIZE / 2.0, -TILE_SIZE / 2.0)
	visual.color = Color(0.25, 0.85, 0.35, 0.75)
	exit_marker.add_child(visual)


func _spawn_player(payload: Dictionary) -> void:
	var spawn_cell: Array = payload.get("spawn_cell", [0, 0])
	var player: CharacterBody2D = PlayerScript.new()
	player.name = "Player"
	player.position = Vector2(spawn_cell[0] * TILE_SIZE, spawn_cell[1] * TILE_SIZE)
	add_child(player)

	var camera: Camera2D = Camera2D.new()
	camera.name = "Camera"
	camera.zoom = Vector2(2.5, 2.5)
	player.add_child(camera)
	# Camera2D.current can only be set once the camera is both inside the
	# tree AND there's a real display server to attach it to - under
	# --headless (Godot's dummy rendering driver, used by CI) setting it
	# raises "Invalid assignment of property or key 'current'", discovered
	# via this project's CI boot-check job. Real editor/gameplay use (a
	# human pressing Play) always has a real DisplayServer, so this only
	# skips activation in the headless CI environment.
	if DisplayServer.get_name() != "headless":
		camera.current = true


func _build_debug_label(result: Dictionary, payload: Dictionary) -> void:
	var canvas: CanvasLayer = CanvasLayer.new()
	add_child(canvas)

	var label: Label = Label.new()
	label.position = Vector2(12, 12)
	label.text = "Recipe: %s   Seed: %d\nWASD / Arrow keys to move" % [
		result.get("recipe_id", "?"),
		int(payload.get("seed", -1)),
	]
	canvas.add_child(label)


func _decode_grid_rle(encoded: String, width: int, height: int) -> PackedByteArray:
	# Decode RLE-encoded grid (v1 format): "rle-v1:<count>:<value>:...".
	# Mirrors fung_export_service.gd's _decode_grid() exactly, since this
	# script and that service both need to agree with bridge/generation.py's
	# encode_grid_rle() - see docs/bridge_protocol.md.
	if not encoded.begins_with("rle-v1:"):
		return PackedByteArray()

	var parts: PackedStringArray = encoded.split(":")
	var result: PackedByteArray = PackedByteArray()

	var i: int = 1  # Skip "rle-v1"
	while i < parts.size():
		if i + 1 < parts.size():
			var count: int = int(parts[i])
			var value: int = int(parts[i + 1])
			for _j in range(count):
				result.append(value)
			i += 2
		else:
			break

	var expected_size: int = width * height
	if result.size() != expected_size:
		push_error("Grid size mismatch: got %d, expected %d" % [result.size(), expected_size])
		return PackedByteArray()

	return result


func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}

	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}

	var text: String = file.get_as_text()
	var json: JSON = JSON.new()
	var error: Error = json.parse(text)
	if error != OK:
		return {}

	var data: Variant = json.data
	if data is Dictionary:
		return data

	return {}
