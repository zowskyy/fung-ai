extends RefCounted
class_name AnimationSceneModel

# ---------------------------------------------------------------------------
# AnimationSceneModel
#
# Pure, editor-independent data model + JSON serialization for the scene
# format consumed by AnimationEngine.gd (see example_scene.json for the
# reference shape: {duration_s, layers: [{name, image, depth, sway:
# {amplitude_deg, speed}}], camera: {loop, keyframes: [{t, x, y, zoom}]}}).
#
# Split out from AnimationEngineDock.gd (the EditorPlugin) so this logic can
# be instantiated and exercised directly with `.new()` outside the editor —
# Godot refuses to instantiate EditorPlugin itself ("can only be instantiated
# by editor"), so this is what makes non-interactive/headless verification
# possible at all. AnimationEngineDock.gd holds one of these and delegates
# to it; the dock's UI is just a thin view over this model.
# ---------------------------------------------------------------------------

var duration_s: float = 8.0
var layers: Array = []            # [{name, image, depth, sway: {amplitude_deg, speed}}]
var camera_loop: bool = false
var camera_keyframes: Array = []  # [{t, x, y, zoom}]


# ---- Layer operations ----

func add_layer(p_name: String, image: String, depth: float = 1.0, amp_deg: float = 0.0, speed: float = 0.0) -> void:
	layers.append({
		"name": p_name,
		"image": image,
		"depth": depth,
		"sway": {"amplitude_deg": amp_deg, "speed": speed},
	})


func remove_layer(idx: int) -> void:
	if idx < 0 or idx >= layers.size():
		return
	layers.remove_at(idx)


func move_layer(idx: int, direction: int) -> void:
	var target := idx + direction
	if idx < 0 or idx >= layers.size():
		return
	if target < 0 or target >= layers.size():
		return
	var tmp = layers[idx]
	layers[idx] = layers[target]
	layers[target] = tmp


func update_layer(idx: int, p_name: String, image: String, depth: float, amp_deg: float, speed: float) -> void:
	if idx < 0 or idx >= layers.size():
		return
	layers[idx] = {
		"name": p_name,
		"image": image,
		"depth": depth,
		"sway": {"amplitude_deg": amp_deg, "speed": speed},
	}


func set_duration(v: float) -> void:
	duration_s = v


# ---- Camera keyframe operations ----

func set_camera_loop(v: bool) -> void:
	camera_loop = v


func add_camera_keyframe(t: float, x: float, y: float, zoom: float) -> void:
	camera_keyframes.append({"t": t, "x": x, "y": y, "zoom": zoom})


func remove_camera_keyframe(idx: int) -> void:
	if idx < 0 or idx >= camera_keyframes.size():
		return
	camera_keyframes.remove_at(idx)


func update_camera_keyframe(idx: int, t: float, x: float, y: float, zoom: float) -> void:
	if idx < 0 or idx >= camera_keyframes.size():
		return
	camera_keyframes[idx] = {"t": t, "x": x, "y": y, "zoom": zoom}


# ---- JSON serialization ----

func to_dict() -> Dictionary:
	var layers_copy: Array = []
	for layer in layers:
		layers_copy.append((layer as Dictionary).duplicate(true))
	var kfs_copy: Array = []
	for kf in camera_keyframes:
		kfs_copy.append((kf as Dictionary).duplicate(true))
	return {
		"duration_s": duration_s,
		"layers": layers_copy,
		"camera": {
			"loop": camera_loop,
			"keyframes": kfs_copy,
		},
	}


func from_dict(data: Dictionary) -> void:
	duration_s = float(data.get("duration_s", 8.0))
	layers = []
	for layer in data.get("layers", []):
		var l: Dictionary = layer
		var sway: Dictionary = l.get("sway", {})
		layers.append({
			"name": String(l.get("name", "layer")),
			"image": String(l.get("image", "")),
			"depth": float(l.get("depth", 1.0)),
			"sway": {
				"amplitude_deg": float(sway.get("amplitude_deg", 0.0)),
				"speed": float(sway.get("speed", 0.0)),
			},
		})
	var cam: Dictionary = data.get("camera", {})
	camera_loop = bool(cam.get("loop", false))
	camera_keyframes = []
	for kf in cam.get("keyframes", []):
		var k: Dictionary = kf
		camera_keyframes.append({
			"t": float(k.get("t", 0.0)),
			"x": float(k.get("x", 0.0)),
			"y": float(k.get("y", 0.0)),
			"zoom": float(k.get("zoom", 1.0)),
		})


func load_json(path: String) -> bool:
	if not FileAccess.file_exists(path):
		push_error("File does not exist: " + path)
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		push_error("Failed to open: " + path)
		return false
	var text := f.get_as_text()
	f.close()
	var parsed = JSON.parse_string(text)
	if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
		push_error("JSON parse failed for " + path)
		return false
	from_dict(parsed)
	return true


func save_json(path: String) -> bool:
	var text := JSON.stringify(to_dict(), "  ")
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		push_error("Failed to open for write: " + path)
		return false
	f.store_string(text)
	f.close()
	return true
