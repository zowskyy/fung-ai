class_name WorldGenerationJob
extends RefCounted

signal completed(result: Dictionary)
signal failed(error: String)
signal progress(value: float)

var _thread: Thread
var _cancelled := false
var _mutex := Mutex.new()


func start(config: Dictionary) -> void:
	_cancelled = false
	_thread = Thread.new()
	_thread.start(_run_generation.bind(config))


func cancel() -> void:
	_mutex.lock()
	_cancelled = true
	_mutex.unlock()
	if _thread != null and _thread.is_started():
		_thread.wait_to_finish()


func _is_cancelled() -> bool:
	_mutex.lock()
	var value := _cancelled
	_mutex.unlock()
	return value


func _run_generation(config: Dictionary) -> void:
	if _is_cancelled():
		return
	progress.emit.call_deferred(0.1)

	if _is_cancelled():
		return

	var result: Dictionary = {}
	var error_message := ""

	if config.has("world_json_path"):
		var load_result := _load_world_from_path(config.world_json_path)
		if load_result.has("error"):
			error_message = load_result.error
		else:
			result = load_result.result
	else:
		result = _generate_world(config)

	if _is_cancelled():
		return
	progress.emit.call_deferred(0.75)

	if _is_cancelled():
		return

	if not error_message.is_empty():
		if not _is_cancelled():
			failed.emit.call_deferred(error_message)
		return

	var validation_error := _validate_world(result)
	if not validation_error.is_empty():
		if not _is_cancelled():
			failed.emit.call_deferred(validation_error)
		return

	if _is_cancelled():
		return
	progress.emit.call_deferred(1.0)

	if not _is_cancelled():
		completed.emit.call_deferred(result)


func _load_world_from_path(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"error": "World file not found: %s" % path}

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {"error": "Failed to open world file (%s): %s" % [error_string(FileAccess.get_open_error()), path]}

	var text := file.get_as_text()
	file.close()

	var parsed = JSON.parse_string(text)
	if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
		return {"error": "Malformed world JSON at %s" % path}

	return {"result": parsed}


func _generate_world(config: Dictionary) -> Dictionary:
	var seed_value: int = config.get("seed", 0)
	var width: int = config.get("width", 5)
	var height: int = config.get("height", 5)

	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value

	var tiles: Array = []
	tiles.resize(width * height)
	for y in height:
		for x in width:
			var idx := y * width + x
			var is_border := x == 0 or y == 0 or x == width - 1 or y == height - 1
			tiles[idx] = 1 if is_border else 0

	var interior_count := maxi(0, (width - 2) * (height - 2))
	var extra_walls := mini(interior_count / 4, interior_count)
	var placed := 0
	var attempts := 0
	var max_attempts := extra_walls * 20 + 20
	while placed < extra_walls and attempts < max_attempts:
		attempts += 1
		var rx := rng.randi_range(1, width - 2)
		var ry := rng.randi_range(1, height - 2)
		var idx := ry * width + rx
		if tiles[idx] == 0:
			tiles[idx] = 1
			placed += 1

	var spawns: Array = []
	var excluded: Array = []

	var player_pos = _find_floor_tile(tiles, width, height, excluded)
	if player_pos != null:
		excluded.append(player_pos)
		spawns.append({"id": "player_spawn", "x": player_pos.x, "y": player_pos.y, "type": "player"})

	var exit_pos = _find_floor_tile(tiles, width, height, excluded)
	if exit_pos != null:
		excluded.append(exit_pos)
		spawns.append({"id": "exit_spawn", "x": exit_pos.x, "y": exit_pos.y, "type": "exit"})

	var boss_pos = _find_floor_tile(tiles, width, height, excluded)
	if boss_pos != null:
		excluded.append(boss_pos)
		spawns.append({"id": "boss_spawn", "x": boss_pos.x, "y": boss_pos.y, "type": "boss"})

	return {
		"version": 1,
		"id": "generated_world_%d" % seed_value,
		"seed": seed_value,
		"width": width,
		"height": height,
		"tiles": tiles,
		"spawns": spawns,
	}


func _find_floor_tile(tiles: Array, width: int, height: int, exclude: Array):
	for y in range(1, height - 1):
		for x in range(1, width - 1):
			var idx := y * width + x
			if tiles[idx] == 0 and not _pos_in_list(x, y, exclude):
				return {"x": x, "y": y}
	for y in height:
		for x in width:
			var idx := y * width + x
			if tiles[idx] == 0 and not _pos_in_list(x, y, exclude):
				return {"x": x, "y": y}
	return null


func _pos_in_list(x: int, y: int, list: Array) -> bool:
	for p in list:
		if p != null and p.x == x and p.y == y:
			return true
	return false


func _validate_world(result: Dictionary) -> String:
	var required_keys := ["version", "id", "width", "height", "tiles", "spawns"]
	for key in required_keys:
		if not result.has(key):
			return "World data missing required key: %s" % key

	var width: int = result.width
	var height: int = result.height
	var tiles: Array = result.tiles
	if tiles.size() != width * height:
		return "Tile count %d does not match width*height (%d)" % [tiles.size(), width * height]

	var spawns: Array = result.spawns
	if spawns.is_empty():
		return "World data has no spawns"

	return ""
