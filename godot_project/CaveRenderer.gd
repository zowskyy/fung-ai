extends Node2D

# Default paths, overridable via command line user args (after "--"):
#   godot --headless --path <project> -- <scene_json_path> <screenshot_output_path>
var scene_json_path := "C:/Users/thewi/OneDrive/Desktop/fung.us/fungaiV2_extracted/godot_scene.json"
var screenshot_path := "C:/Users/thewi/OneDrive/Desktop/fung.us/godot_project/screenshot.png"

const WALL_COLOR := Color(0.15, 0.13, 0.12)
const FLOOR_COLOR := Color(0.82, 0.76, 0.62)
const PLAYER_COLOR := Color(0.1, 0.9, 0.2)
const ENEMY_COLOR := Color(0.95, 0.1, 0.1)

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() >= 1:
		scene_json_path = args[0]
	if args.size() >= 2:
		screenshot_path = args[1]

	print("Loading scene JSON from: ", scene_json_path)

	var loaded = load_scene_data(scene_json_path)
	if loaded == null:
		push_error("Failed to load/parse scene JSON at %s" % scene_json_path)
		get_tree().quit(1)
		return

	build_visuals(loaded)

	# Wait a couple of frames so everything is actually drawn/composited
	# before we grab the viewport texture.
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame

	var img := get_viewport().get_texture().get_image()
	var err := img.save_png(screenshot_path)
	if err == OK:
		print("Screenshot saved to: ", screenshot_path)
	else:
		push_error("Failed to save screenshot, error code: %s" % err)

	get_tree().quit()


func load_scene_data(path: String):
	if not FileAccess.file_exists(path):
		push_error("File does not exist: " + path)
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	var text := f.get_as_text()
	f.close()
	var parsed = JSON.parse_string(text)
	if parsed == null:
		push_error("JSON parse failed for " + path)
		return null
	return parsed


func build_visuals(data: Dictionary) -> void:
	var tile_size := 32
	if data.has("metadata") and data["metadata"].has("tile_size"):
		tile_size = int(data["metadata"]["tile_size"])

	var tilemap: Array = data.get("tilemap", [])
	print("Tile count: ", tilemap.size())

	for tile in tilemap:
		var rect := ColorRect.new()
		rect.position = Vector2(float(tile["x"]), float(tile["y"]))
		rect.size = Vector2(tile_size, tile_size)
		if tile["type"] == "wall":
			rect.color = WALL_COLOR
		else:
			rect.color = FLOOR_COLOR
		add_child(rect)

	if data.has("player_spawn"):
		var ps = data["player_spawn"]
		var marker := ColorRect.new()
		marker.size = Vector2(tile_size * 0.6, tile_size * 0.6)
		marker.position = Vector2(float(ps["x"]) - marker.size.x / 2.0, float(ps["y"]) - marker.size.y / 2.0)
		marker.color = PLAYER_COLOR
		add_child(marker)

	if data.has("enemy_spawns"):
		for es in data["enemy_spawns"]:
			var marker := ColorRect.new()
			marker.size = Vector2(tile_size * 0.5, tile_size * 0.5)
			marker.position = Vector2(float(es["x"]) - marker.size.x / 2.0, float(es["y"]) - marker.size.y / 2.0)
			marker.color = ENEMY_COLOR
			add_child(marker)

	print("Built visuals: %d tiles, player_spawn=%s, enemy_spawns=%d" % [
		tilemap.size(),
		str(data.get("player_spawn", null)),
		data.get("enemy_spawns", []).size()
	])
