extends SceneTree

# Non-interactive verification harness for the scene-composition GUI
# (AnimationEngineDock.gd + AnimationSceneModel.gd).
#
# Godot refuses to instantiate EditorPlugin outside the actual editor
# ("can only be instantiated by editor"), so this exercises the plugin's
# data model directly: AnimationSceneModel.gd is a plain RefCounted class
# that AnimationEngineDock.gd's UI callbacks delegate to one-for-one (see
# _on_add_layer_pressed, _on_update_layer_pressed, etc. in
# AnimationEngineDock.gd — each is a thin wrapper calling the same model
# methods exercised below plus a UI refresh). Exercising the model this way
# is equivalent to exercising the dock's add-layer/edit-keyframe/save-JSON
# logic through its buttons.
#
# Run with:
#   Godot_v4.7.1-stable_win64_console.exe --headless --path <project> --script test_dock_headless.gd

const OUT_PATH := "C:/Users/thewi/OneDrive/Desktop/fung.us/godot_project/dock_test_output.json"

func _init() -> void:
	var ok := true

	var ModelScript := load("res://AnimationSceneModel.gd")
	var dock = ModelScript.new()

	# --- exercise layer operations ---
	dock.add_layer("sky", "placeholder_layers/sky.png", 0.1, 0.0, 0.0)
	dock.add_layer("hills", "placeholder_layers/hills.png", 0.4, 1.5, 0.4)
	dock.add_layer("temp_layer", "placeholder_layers/foreground.png", 1.0, 3.0, 1.1)
	ok = ok and _check(dock.layers.size() == 3, "expected 3 layers after add")

	# reorder: move temp_layer (idx 2) up to idx 1
	dock.move_layer(2, -1)
	ok = ok and _check(dock.layers[1]["name"] == "temp_layer", "move_layer did not reorder correctly")

	# move it back down and then update it in place to "foreground"
	dock.move_layer(1, 1)
	ok = ok and _check(dock.layers[2]["name"] == "temp_layer", "move_layer back down failed")
	dock.update_layer(2, "foreground", "placeholder_layers/foreground.png", 1.0, 3.0, 1.1)
	ok = ok and _check(dock.layers[2]["name"] == "foreground", "update_layer failed to rename")
	ok = ok and _check(dock.layers[2]["sway"]["amplitude_deg"] == 3.0, "update_layer sway amplitude mismatch")

	# --- exercise camera keyframe operations ---
	dock.set_camera_loop(true)
	dock.add_camera_keyframe(0.0, 0.0, 0.0, 1.0)
	dock.add_camera_keyframe(4.0, 999.0, 0.0, 1.15)  # deliberately wrong, will fix via update
	dock.add_camera_keyframe(8.0, 0.0, 0.0, 1.0)
	ok = ok and _check(dock.camera_keyframes.size() == 3, "expected 3 camera keyframes")
	dock.update_camera_keyframe(1, 4.0, 220.0, 0.0, 1.15)
	ok = ok and _check(dock.camera_keyframes[1]["x"] == 220.0, "update_camera_keyframe failed")

	dock.remove_camera_keyframe(2)
	ok = ok and _check(dock.camera_keyframes.size() == 2, "remove_camera_keyframe failed")
	dock.add_camera_keyframe(8.0, 0.0, 0.0, 1.0)

	dock.set_duration(8.0)

	# --- save JSON and validate shape ---
	var saved: bool = dock.save_json(OUT_PATH)
	ok = ok and _check(saved, "save_json reported failure")

	var f := FileAccess.open(OUT_PATH, FileAccess.READ)
	var text := f.get_as_text()
	f.close()
	var parsed = JSON.parse_string(text)
	ok = ok and _check(parsed != null, "produced JSON failed to parse")
	ok = ok and _check(typeof(parsed) == TYPE_DICTIONARY, "produced JSON is not an object")
	ok = ok and _check(parsed.has("duration_s") and parsed.has("layers") and parsed.has("camera"), "missing top-level keys")
	ok = ok and _check(parsed["layers"].size() == 3, "expected 3 layers in saved JSON")
	for layer in parsed["layers"]:
		ok = ok and _check(layer.has("name") and layer.has("image") and layer.has("depth") and layer.has("sway"), "layer missing required keys: %s" % [layer])
		ok = ok and _check(layer["sway"].has("amplitude_deg") and layer["sway"].has("speed"), "sway missing keys")
	ok = ok and _check(parsed["camera"].has("loop") and parsed["camera"].has("keyframes"), "camera missing keys")
	ok = ok and _check(parsed["camera"]["loop"] == true, "camera loop should be true")
	ok = ok and _check(parsed["camera"]["keyframes"].size() == 3, "expected 3 keyframes in saved JSON")
	for kf in parsed["camera"]["keyframes"]:
		ok = ok and _check(kf.has("t") and kf.has("x") and kf.has("y") and kf.has("zoom"), "keyframe missing required keys: %s" % [kf])

	# --- round trip: load it back into a fresh model instance ---
	var dock2 = ModelScript.new()
	var loaded: bool = dock2.load_json(OUT_PATH)
	ok = ok and _check(loaded, "load_json reported failure")
	ok = ok and _check(dock2.layers.size() == 3, "round-trip layer count mismatch")
	ok = ok and _check(dock2.camera_keyframes.size() == 3, "round-trip keyframe count mismatch")
	ok = ok and _check(dock2.layers[0]["name"] == "sky", "round-trip layer name mismatch")
	ok = ok and _check(dock2.camera_keyframes[1]["x"] == 220.0, "round-trip keyframe value mismatch")

	if ok:
		print("DOCK_TEST_RESULT: PASS")
	else:
		print("DOCK_TEST_RESULT: FAIL")

	quit(0 if ok else 1)


func _check(cond: bool, msg: String) -> bool:
	if not cond:
		print("ASSERTION FAILED: ", msg)
	return cond
