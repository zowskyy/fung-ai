@tool
extends Node

class_name FungExportService

## Exports generated candidates to editable TileMapLayer scenes.

signal export_started(candidate_id: String)
signal export_progress(candidate_id: String, progress: float, message: String)
signal export_completed(candidate_id: String, success: bool, scene_path: String)

var _export_root: String = "user://generated/fung/"


# Export a single candidate to a TileMapLayer scene.
#   result_path: path to result.json from generation
#   candidate_id: candidate ID to export (e.g. "candidate_001")
#   tileset_path: path to TileSet resource (res://...)
#   export_profile: export profile name (top_down_default, platformer_default, etc.)
# Returns true if the scene was written successfully.
func export_candidate(
	result_path: String,
	candidate_id: String,
	tileset_path: String,
	export_profile: String = "top_down_default",
) -> bool:
	if not ResourceLoader.exists(tileset_path):
		push_error("TileSet not found: %s" % tileset_path)
		return false

	export_started.emit(candidate_id)

	var result_data: Dictionary = _read_json_safe(result_path)
	if result_data.is_empty():
		export_completed.emit(candidate_id, false, "")
		return false

	var candidate: Dictionary = {}
	for cand in result_data.get("candidates", []):
		if cand.get("candidate_id") == candidate_id:
			candidate = cand
			break

	if candidate.is_empty():
		push_error("Candidate not found: %s" % candidate_id)
		export_completed.emit(candidate_id, false, "")
		return false

	# result.json has no job_dir field; the job directory is always the
	# parent directory of result.json itself, and candidate paths (payload,
	# preview) are stored relative to it.
	var job_dir: String = result_path.get_base_dir()
	var payload_path: String = job_dir.path_join(candidate.get("payload_path", ""))
	var payload: Dictionary = _read_json_safe(payload_path)

	if payload.is_empty():
		push_error("Candidate payload not found: %s" % payload_path)
		export_completed.emit(candidate_id, false, "")
		return false

	var scene: Node2D = _build_scene(candidate, payload, tileset_path, export_profile)
	if scene == null:
		export_completed.emit(candidate_id, false, "")
		return false

	var scene_path: String = _get_export_scene_path(candidate_id)
	DirAccess.make_dir_recursive_absolute(scene_path.get_base_dir())

	var packed_scene: PackedScene = PackedScene.new()
	var pack_error: Error = packed_scene.pack(scene)
	if pack_error != OK:
		push_error("Failed to pack scene: %s (error code %d)" % [scene_path, pack_error])
		scene.queue_free()
		export_completed.emit(candidate_id, false, "")
		return false

	var save_error: Error = ResourceSaver.save(packed_scene, scene_path)
	scene.queue_free()

	if save_error != OK:
		push_error("Failed to save scene: %s (error code %d)" % [scene_path, save_error])
		export_completed.emit(candidate_id, false, "")
		return false

	export_progress.emit(candidate_id, 1.0, "Scene exported")
	export_completed.emit(candidate_id, true, scene_path)
	return true


func _build_scene(
	candidate: Dictionary,
	payload: Dictionary,
	tileset_path: String,
	export_profile: String,
) -> Node2D:
	"""Build Node2D scene from candidate payload."""
	var root: Node2D = Node2D.new()
	root.name = candidate.get("candidate_id", "GeneratedLevel")

	# Decode grid
	var grid_size: Array = payload.get("grid_size", [96, 96])
	var width: int = int(grid_size[0])
	var height: int = int(grid_size[1])
	var grid: PackedByteArray = _decode_grid(payload.get("grid", ""), width, height)

	if grid.is_empty():
		push_error("Failed to decode grid")
		return null

	# Create TileMapLayer for walls/floor
	var tilemap: TileMapLayer = TileMapLayer.new()
	tilemap.name = "Terrain"
	tilemap.tile_set = ResourceLoader.load(tileset_path)

	# Set tiles from grid (1=wall, 0=floor)
	for y in range(height):
		for x in range(width):
			var cell_idx: int = y * width + x
			if cell_idx < grid.size():
				var is_wall: int = grid[cell_idx]
				# Wall=1 maps to tile_id 1, Floor=0 maps to tile_id 0
				tilemap.set_cell(Vector2i(x, y), 0, Vector2i(is_wall, 0))

	root.add_child(tilemap)

	# Add spawn marker
	var spawn_cell: Array = payload.get("spawn_cell", [0, 0])
	var spawn_marker: Marker2D = Marker2D.new()
	spawn_marker.name = "PlayerSpawn"
	spawn_marker.position = Vector2(spawn_cell[0] * 16, spawn_cell[1] * 16)
	root.add_child(spawn_marker)

	# Add exit marker
	var exit_cell: Array = payload.get("exit_cell", [95, 95])
	var exit_marker: Marker2D = Marker2D.new()
	exit_marker.name = "Exit"
	exit_marker.position = Vector2(exit_cell[0] * 16, exit_cell[1] * 16)
	root.add_child(exit_marker)

	# Add gameplay markers container
	var markers_node: Node2D = Node2D.new()
	markers_node.name = "GameplayMarkers"

	var markers: Dictionary = payload.get("markers", {})
	var arena_candidates: Array = markers.get("arena_candidates", [])
	var loot_candidates: Array = markers.get("loot_candidates", [])

	for idx in range(arena_candidates.size()):
		var cell: Array = arena_candidates[idx]
		var marker: Marker2D = Marker2D.new()
		marker.name = "ArenaCandidate_%03d" % (idx + 1)
		marker.position = Vector2(cell[0] * 16, cell[1] * 16)
		markers_node.add_child(marker)

	for idx in range(loot_candidates.size()):
		var cell: Array = loot_candidates[idx]
		var marker: Marker2D = Marker2D.new()
		marker.name = "LootCandidate_%03d" % (idx + 1)
		marker.position = Vector2(cell[0] * 16, cell[1] * 16)
		markers_node.add_child(marker)

	root.add_child(markers_node)

	return root


func _decode_grid(encoded: String, width: int, height: int) -> PackedByteArray:
	"""Decode RLE-encoded grid (v1 format).

	Format: "rle-v1:<count>:<value>:<count>:<value>:..."
	Example: "rle-v1:10:0:5:1" = 10 zeros, 5 ones
	"""
	if not encoded.begins_with("rle-v1:"):
		# Fallback: assume it's raw bytes (hex-encoded or similar)
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

	# Validate grid size
	var expected_size: int = width * height
	if result.size() != expected_size:
		push_error("Grid size mismatch: got %d, expected %d" % [result.size(), expected_size])
		return PackedByteArray()

	return result


func _read_json_safe(path: String) -> Dictionary:
	"""Safely read and parse JSON file."""
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


func _get_export_scene_path(candidate_id: String) -> String:
	"""Get export path for a candidate scene."""
	return _export_root.path_join("levels").path_join(candidate_id + ".tscn")
