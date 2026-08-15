@tool
extends EditorPlugin

# ---------------------------------------------------------------------------
# AnimationEngineDock
#
# Visual scene-composition tool for the scene JSON format consumed by
# AnimationEngine.gd. Lets you add/reorder/remove layers, edit depth/sway,
# edit camera keyframes, and load/save the JSON — all without hand-editing it.
#
# All actual scene data + JSON I/O lives in AnimationSceneModel.gd (a plain
# RefCounted class), not here. Godot refuses to instantiate EditorPlugin
# outside the editor ("can only be instantiated by editor"), so the model
# is what makes non-interactive/headless verification of this feature
# possible: instantiate AnimationSceneModel.gd with `.new()` in a headless
# test scene, call add_layer/move_layer/add_camera_keyframe/save_json/etc
# directly, and inspect the JSON it produces. This script is a thin
# EditorPlugin shell — UI plus editor-only wiring (dock registration,
# play_custom_scene) — over that model.
# ---------------------------------------------------------------------------

const SceneModel := preload("res://AnimationSceneModel.gd")

var model: AnimationSceneModel
var current_json_path: String = ""

# ---- UI state ---------------------------------------------------------

var dock: Control
var path_edit: LineEdit
var duration_spin: SpinBox
var layer_list: ItemList
var name_edit: LineEdit
var image_edit: LineEdit
var depth_spin: SpinBox
var amp_spin: SpinBox
var speed_spin: SpinBox
var loop_check: CheckBox
var kf_list: ItemList
var t_spin: SpinBox
var x_spin: SpinBox
var y_spin: SpinBox
var zoom_spin: SpinBox
var status_label: Label

var selected_layer_idx: int = -1
var selected_kf_idx: int = -1


# ---------------------------------------------------------------------------
# Editor plugin lifecycle
# ---------------------------------------------------------------------------

func _enter_tree() -> void:
	model = SceneModel.new()
	dock = _build_dock_ui()
	add_control_to_dock(EditorPlugin.DOCK_SLOT_LEFT_UR, dock)


func _exit_tree() -> void:
	if dock:
		remove_control_from_docks(dock)
		dock.queue_free()
		dock = null


# ---------------------------------------------------------------------------
# UI construction
# ---------------------------------------------------------------------------

func _build_dock_ui() -> Control:
	var root := VBoxContainer.new()
	root.name = "AnimationEngineDock"

	var title := Label.new()
	title.text = "Animation Scene Composer"
	root.add_child(title)

	# --- JSON path + load/save ---
	var path_row := HBoxContainer.new()
	path_edit = LineEdit.new()
	path_edit.placeholder_text = "path to scene JSON"
	path_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	path_row.add_child(path_edit)
	var load_btn := Button.new()
	load_btn.text = "Load JSON"
	load_btn.pressed.connect(_on_load_pressed)
	path_row.add_child(load_btn)
	var save_btn := Button.new()
	save_btn.text = "Save JSON"
	save_btn.pressed.connect(_on_save_pressed)
	path_row.add_child(save_btn)
	root.add_child(path_row)

	# --- duration ---
	var dur_row := HBoxContainer.new()
	dur_row.add_child(_label("Duration (s):"))
	duration_spin = SpinBox.new()
	duration_spin.min_value = 0
	duration_spin.max_value = 3600
	duration_spin.step = 0.1
	duration_spin.value = model.duration_s
	duration_spin.value_changed.connect(func(v): model.set_duration(v))
	dur_row.add_child(duration_spin)
	root.add_child(dur_row)

	root.add_child(HSeparator.new())
	root.add_child(_label("Layers"))

	layer_list = ItemList.new()
	layer_list.custom_minimum_size = Vector2(0, 100)
	layer_list.item_selected.connect(_on_layer_selected)
	root.add_child(layer_list)

	var layer_btn_row := HBoxContainer.new()
	var add_layer_btn := Button.new()
	add_layer_btn.text = "Add"
	add_layer_btn.pressed.connect(_on_add_layer_pressed)
	layer_btn_row.add_child(add_layer_btn)
	var remove_layer_btn := Button.new()
	remove_layer_btn.text = "Remove"
	remove_layer_btn.pressed.connect(_on_remove_layer_pressed)
	layer_btn_row.add_child(remove_layer_btn)
	var up_btn := Button.new()
	up_btn.text = "Up"
	up_btn.pressed.connect(func(): _on_move_layer_pressed(-1))
	layer_btn_row.add_child(up_btn)
	var down_btn := Button.new()
	down_btn.text = "Down"
	down_btn.pressed.connect(func(): _on_move_layer_pressed(1))
	layer_btn_row.add_child(down_btn)
	root.add_child(layer_btn_row)

	name_edit = LineEdit.new()
	name_edit.placeholder_text = "layer name"
	root.add_child(name_edit)
	image_edit = LineEdit.new()
	image_edit.placeholder_text = "image path (relative to JSON)"
	root.add_child(image_edit)

	var depth_row := HBoxContainer.new()
	depth_row.add_child(_label("Depth:"))
	depth_spin = SpinBox.new()
	depth_spin.min_value = 0
	depth_spin.max_value = 10
	depth_spin.step = 0.01
	depth_spin.value = 1.0
	depth_row.add_child(depth_spin)
	root.add_child(depth_row)

	var sway_row := HBoxContainer.new()
	sway_row.add_child(_label("Sway amp (deg):"))
	amp_spin = SpinBox.new()
	amp_spin.min_value = -180
	amp_spin.max_value = 180
	amp_spin.step = 0.1
	sway_row.add_child(amp_spin)
	sway_row.add_child(_label("speed:"))
	speed_spin = SpinBox.new()
	speed_spin.min_value = -100
	speed_spin.max_value = 100
	speed_spin.step = 0.01
	sway_row.add_child(speed_spin)
	root.add_child(sway_row)

	var update_layer_btn := Button.new()
	update_layer_btn.text = "Update Selected Layer"
	update_layer_btn.pressed.connect(_on_update_layer_pressed)
	root.add_child(update_layer_btn)

	root.add_child(HSeparator.new())
	root.add_child(_label("Camera"))

	loop_check = CheckBox.new()
	loop_check.text = "Loop"
	loop_check.toggled.connect(func(v): model.set_camera_loop(v))
	root.add_child(loop_check)

	kf_list = ItemList.new()
	kf_list.custom_minimum_size = Vector2(0, 100)
	kf_list.item_selected.connect(_on_kf_selected)
	root.add_child(kf_list)

	var kf_btn_row := HBoxContainer.new()
	var add_kf_btn := Button.new()
	add_kf_btn.text = "Add"
	add_kf_btn.pressed.connect(_on_add_kf_pressed)
	kf_btn_row.add_child(add_kf_btn)
	var remove_kf_btn := Button.new()
	remove_kf_btn.text = "Remove"
	remove_kf_btn.pressed.connect(_on_remove_kf_pressed)
	kf_btn_row.add_child(remove_kf_btn)
	root.add_child(kf_btn_row)

	var kf_row1 := HBoxContainer.new()
	kf_row1.add_child(_label("t:"))
	t_spin = _make_free_spin()
	kf_row1.add_child(t_spin)
	kf_row1.add_child(_label("x:"))
	x_spin = _make_free_spin()
	kf_row1.add_child(x_spin)
	root.add_child(kf_row1)

	var kf_row2 := HBoxContainer.new()
	kf_row2.add_child(_label("y:"))
	y_spin = _make_free_spin()
	kf_row2.add_child(y_spin)
	kf_row2.add_child(_label("zoom:"))
	zoom_spin = _make_free_spin()
	zoom_spin.value = 1.0
	kf_row2.add_child(zoom_spin)
	root.add_child(kf_row2)

	var update_kf_btn := Button.new()
	update_kf_btn.text = "Update Selected Keyframe"
	update_kf_btn.pressed.connect(_on_update_kf_pressed)
	root.add_child(update_kf_btn)

	root.add_child(HSeparator.new())

	status_label = Label.new()
	status_label.text = ""
	status_label.autowrap_mode = TextServer.AUTOWRAP_WORD
	root.add_child(status_label)

	return root


func _label(text: String) -> Label:
	var l := Label.new()
	l.text = text
	return l


func _make_free_spin() -> SpinBox:
	var s := SpinBox.new()
	s.min_value = -100000
	s.max_value = 100000
	s.step = 0.01
	s.allow_greater = true
	s.allow_lesser = true
	return s


func _set_status(text: String) -> void:
	if status_label:
		status_label.text = text
	print("[AnimationEngineDock] ", text)


func _refresh_layer_ui() -> void:
	if not layer_list:
		return
	layer_list.clear()
	for layer in model.layers:
		var sway: Dictionary = layer.get("sway", {})
		layer_list.add_item("%s (depth=%.2f, sway=%.1fdeg@%.2f)" % [
			layer.get("name", ""), float(layer.get("depth", 1.0)),
			float(sway.get("amplitude_deg", 0.0)), float(sway.get("speed", 0.0))
		])


func _refresh_kf_ui() -> void:
	if not kf_list:
		return
	kf_list.clear()
	for kf in model.camera_keyframes:
		kf_list.add_item("t=%.2f x=%.1f y=%.1f zoom=%.2f" % [
			float(kf.get("t", 0.0)), float(kf.get("x", 0.0)),
			float(kf.get("y", 0.0)), float(kf.get("zoom", 1.0))
		])


func _refresh_all_ui() -> void:
	_refresh_layer_ui()
	_refresh_kf_ui()
	if duration_spin:
		duration_spin.value = model.duration_s
	if loop_check:
		loop_check.button_pressed = model.camera_loop


# ---------------------------------------------------------------------------
# UI callbacks — thin wrappers that delegate to `model` and refresh views
# ---------------------------------------------------------------------------

func _on_load_pressed() -> void:
	if model.load_json(path_edit.text):
		current_json_path = path_edit.text
		selected_layer_idx = -1
		selected_kf_idx = -1
		_refresh_all_ui()
		_set_status("Loaded: " + path_edit.text)
	else:
		_set_status("Failed to load: " + path_edit.text)


func _on_save_pressed() -> void:
	if path_edit.text == "":
		_set_status("Enter a JSON path first.")
		return
	if model.save_json(path_edit.text):
		current_json_path = path_edit.text
		_set_status("Saved: " + path_edit.text)
	else:
		_set_status("Failed to save: " + path_edit.text)


func _on_add_layer_pressed() -> void:
	model.add_layer("new_layer", "path/to/image.png", 1.0, 0.0, 0.0)
	_refresh_layer_ui()


func _on_remove_layer_pressed() -> void:
	model.remove_layer(selected_layer_idx)
	selected_layer_idx = -1
	_refresh_layer_ui()


func _on_move_layer_pressed(direction: int) -> void:
	model.move_layer(selected_layer_idx, direction)
	selected_layer_idx += direction
	_refresh_layer_ui()


func _on_update_layer_pressed() -> void:
	if selected_layer_idx < 0:
		_set_status("Select a layer first.")
		return
	model.update_layer(selected_layer_idx, name_edit.text, image_edit.text,
		depth_spin.value, amp_spin.value, speed_spin.value)
	_refresh_layer_ui()


func _on_layer_selected(index: int) -> void:
	selected_layer_idx = index
	if index < 0 or index >= model.layers.size():
		return
	var layer: Dictionary = model.layers[index]
	var sway: Dictionary = layer.get("sway", {})
	name_edit.text = String(layer.get("name", ""))
	image_edit.text = String(layer.get("image", ""))
	depth_spin.value = float(layer.get("depth", 1.0))
	amp_spin.value = float(sway.get("amplitude_deg", 0.0))
	speed_spin.value = float(sway.get("speed", 0.0))


func _on_add_kf_pressed() -> void:
	model.add_camera_keyframe(0.0, 0.0, 0.0, 1.0)
	_refresh_kf_ui()


func _on_remove_kf_pressed() -> void:
	model.remove_camera_keyframe(selected_kf_idx)
	selected_kf_idx = -1
	_refresh_kf_ui()


func _on_update_kf_pressed() -> void:
	if selected_kf_idx < 0:
		_set_status("Select a keyframe first.")
		return
	model.update_camera_keyframe(selected_kf_idx, t_spin.value, x_spin.value, y_spin.value, zoom_spin.value)
	_refresh_kf_ui()


func _on_kf_selected(index: int) -> void:
	selected_kf_idx = index
	if index < 0 or index >= model.camera_keyframes.size():
		return
	var kf: Dictionary = model.camera_keyframes[index]
	t_spin.value = float(kf.get("t", 0.0))
	x_spin.value = float(kf.get("x", 0.0))
	y_spin.value = float(kf.get("y", 0.0))
	zoom_spin.value = float(kf.get("zoom", 1.0))


