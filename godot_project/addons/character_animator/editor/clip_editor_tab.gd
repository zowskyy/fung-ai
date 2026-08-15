@tool
extends VBoxContainer
## Dock tab for authoring sprite-frame animation clips on a selected
## CharacterAnimator node: clip list, frame regions picked from the sprite
## sheet, per-clip fps/loop/flip, and a UI-only preview.

const CharacterAnimatorScript := preload("res://addons/character_animator/runtime/character_animator.gd")
const AnimationClipScript := preload("res://addons/character_animator/runtime/animation_clip.gd")
const RegionEditorScript := preload("res://addons/character_animator/editor/texture_region_editor.gd")
const UndoServiceScript := preload("res://addons/character_animator/editor/undo_service.gd")

var editor_interface: EditorInterface
var target: CharacterAnimator = null

var _target_label: Label
var _create_button: Button
var _clip_name_edit: LineEdit
var _add_clip_button: Button
var _clip_list: ItemList
var _rename_button: Button
var _delete_button: Button
var _fps_spin: SpinBox
var _loop_check: CheckBox
var _flip_h_check: CheckBox
var _flip_v_check: CheckBox
var _region: Control
var _frame_list: ItemList
var _add_frame_button: Button
var _update_frame_button: Button
var _remove_frame_button: Button
var _up_frame_button: Button
var _down_frame_button: Button
var _preview_rect: TextureRect
var _play_button: Button
var _pause_button: Button
var _stop_button: Button
var _preview_label: Label

var _preview_clip: AnimationClip = null
var _preview_index := 0
var _preview_time := 0.0
var _preview_playing := false


func _ready() -> void:
	_build_ui()
	_sync_target()


func refresh_target() -> void:
	target = _find_target()
	_sync_target()


func load_clip(clip: AnimationClip) -> void:
	if clip == null:
		return
	var index := _clip_list.get_item_count()
	for i in _clip_list.get_item_count():
		if _clip_list.get_item_text(i) == String(clip.name):
			index = i
			break
	if _clip_list.get_item_count() > 0:
		_clip_list.select(index)
		_on_clip_selected(index)


func _build_ui() -> void:
	_target_label = Label.new()
	_target_label.text = "No CharacterAnimator selected"
	add_child(_target_label)

	_create_button = Button.new()
	_create_button.text = "Create CharacterAnimator on selection"
	_create_button.pressed.connect(_create_animator)
	add_child(_create_button)

	add_child(_separator())

	var clip_row := HBoxContainer.new()
	_clip_name_edit = LineEdit.new()
	_clip_name_edit.placeholder_text = "clip name"
	_add_clip_button = Button.new()
	_add_clip_button.text = "Add Clip"
	_add_clip_button.pressed.connect(_add_clip)
	clip_row.add_child(_clip_name_edit)
	clip_row.add_child(_add_clip_button)
	add_child(clip_row)

	_clip_list = ItemList.new()
	_clip_list.custom_minimum_size = Vector2(0, 90)
	_clip_list.item_selected.connect(_on_clip_selected)
	add_child(_clip_list)

	var clip_actions := HBoxContainer.new()
	_rename_button = Button.new()
	_rename_button.text = "Rename"
	_rename_button.pressed.connect(_rename_clip)
	_delete_button = Button.new()
	_delete_button.text = "Delete"
	_delete_button.pressed.connect(_delete_clip)
	clip_actions.add_child(_rename_button)
	clip_actions.add_child(_delete_button)
	add_child(clip_actions)

	add_child(_separator())

	var props := GridContainer.new()
	props.columns = 2
	var fps_label := Label.new()
	fps_label.text = "FPS"
	_fps_spin = SpinBox.new()
	_fps_spin.min_value = 0.1
	_fps_spin.max_value = 120.0
	_fps_spin.step = 0.1
	_fps_spin.value_changed.connect(func(value: float):
		var clip := _current_clip()
		if clip != null:
			clip.fps = value)
	_loop_check = CheckBox.new()
	_loop_check.text = "Loop"
	_loop_check.toggled.connect(func(value: bool):
		var clip := _current_clip()
		if clip != null:
			clip.loop = value)
	_flip_h_check = CheckBox.new()
	_flip_h_check.text = "Flip H"
	_flip_h_check.toggled.connect(func(value: bool):
		var clip := _current_clip()
		if clip != null:
			clip.flip_h = value)
	_flip_v_check = CheckBox.new()
	_flip_v_check.text = "Flip V"
	_flip_v_check.toggled.connect(func(value: bool):
		var clip := _current_clip()
		if clip != null:
			clip.flip_v = value)
	props.add_child(fps_label)
	props.add_child(_fps_spin)
	props.add_child(_loop_check)
	props.add_child(_flip_h_check)
	props.add_child(_flip_v_check)
	add_child(props)

	add_child(_separator())
	var frames_label := Label.new()
	frames_label.text = "Frames (drag a region in the sheet, then Add Frame)"
	add_child(frames_label)

	_region = RegionEditorScript.new()
	add_child(_region)

	var frame_actions := HBoxContainer.new()
	_add_frame_button = Button.new()
	_add_frame_button.text = "Add Frame"
	_add_frame_button.pressed.connect(_add_frame)
	_update_frame_button = Button.new()
	_update_frame_button.text = "Update"
	_update_frame_button.pressed.connect(_update_frame)
	_remove_frame_button = Button.new()
	_remove_frame_button.text = "Remove"
	_remove_frame_button.pressed.connect(_remove_frame)
	_up_frame_button = Button.new()
	_up_frame_button.text = "Up"
	_up_frame_button.pressed.connect(func(): _move_frame(-1))
	_down_frame_button = Button.new()
	_down_frame_button.text = "Down"
	_down_frame_button.pressed.connect(func(): _move_frame(1))
	frame_actions.add_child(_add_frame_button)
	frame_actions.add_child(_update_frame_button)
	frame_actions.add_child(_remove_frame_button)
	frame_actions.add_child(_up_frame_button)
	frame_actions.add_child(_down_frame_button)
	add_child(frame_actions)

	_frame_list = ItemList.new()
	_frame_list.custom_minimum_size = Vector2(0, 80)
	_frame_list.item_selected.connect(_on_frame_selected)
	add_child(_frame_list)

	add_child(_separator())

	var preview_row := HBoxContainer.new()
	_play_button = Button.new()
	_play_button.text = "Play"
	_play_button.pressed.connect(_start_preview)
	_pause_button = Button.new()
	_pause_button.text = "Pause"
	_pause_button.pressed.connect(_pause_preview)
	_stop_button = Button.new()
	_stop_button.text = "Stop"
	_stop_button.pressed.connect(_stop_preview)
	preview_row.add_child(_play_button)
	preview_row.add_child(_pause_button)
	preview_row.add_child(_stop_button)
	add_child(preview_row)

	_preview_rect = TextureRect.new()
	_preview_rect.custom_minimum_size = Vector2(64, 64)
	_preview_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	add_child(_preview_rect)

	_preview_label = Label.new()
	_preview_label.text = ""
	add_child(_preview_label)


func _separator() -> HSeparator:
	var sep := HSeparator.new()
	sep.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return sep


func _find_target() -> CharacterAnimator:
	if editor_interface == null:
		return null
	for node in editor_interface.get_selection().get_selected_nodes():
		if node is CharacterAnimator:
			return node
	return null


func _create_animator() -> void:
	if editor_interface == null:
		return
	var root := editor_interface.get_edited_scene_root()
	if root == null:
		return
	var parent: Node = root
	var selection := editor_interface.get_selection().get_selected_nodes()
	if not selection.is_empty():
		parent = selection[0]
	var node := Sprite2D.new()
	node.name = "CharacterAnimator"
	node.set_script(CharacterAnimatorScript)
	var undo := UndoServiceScript.new(editor_interface)
	undo.add_node(parent, node, root)
	editor_interface.get_selection().clear()
	editor_interface.get_selection().add_node(node)
	target = node
	_sync_target()


func _sync_target() -> void:
	if target == null:
		_target_label.text = "No CharacterAnimator selected"
		_set_clip_ui_enabled(false)
		_region.texture = null
		_refresh_clip_list()
		_update_preview()
		return
	_target_label.text = "Target: %s (%s)" % [target.name, target.get_parent().get_path_to(target)]
	_region.texture = target.texture
	_set_clip_ui_enabled(true)
	_refresh_clip_list()
	if target.texture != null and target.texture.get_width() > 0:
		_region.region = Rect2(0, 0, float(target.texture.get_width()), float(target.texture.get_height()))


func _set_clip_ui_enabled(enabled: bool) -> void:
	for widget in [
		_clip_name_edit, _add_clip_button, _clip_list, _rename_button, _delete_button,
		_fps_spin, _loop_check, _flip_h_check, _flip_v_check, _region,
		_add_frame_button, _update_frame_button, _remove_frame_button, _up_frame_button,
		_down_frame_button, _frame_list, _play_button, _pause_button, _stop_button,
	]:
		if widget is LineEdit:
			widget.editable = enabled
		elif widget is SpinBox:
			widget.editable = enabled
		elif widget is ItemList:
			widget.mouse_filter = Control.MOUSE_FILTER_IGNORE if not enabled else Control.MOUSE_FILTER_STOP
		else:
			widget.disabled = not enabled


func _refresh_clip_list() -> void:
	_clip_list.clear()
	if target == null:
		return
	for clip_name in target.clips:
		_clip_list.add_item(String(clip_name))
	if _clip_list.get_item_count() > 0:
		_clip_list.select(0)
		_on_clip_selected(0)


func _on_clip_selected(index: int) -> void:
	if index < 0 or index >= _clip_list.get_item_count():
		return
	var clip := _current_clip()
	if clip == null:
		return
	_fps_spin.set_value_no_signal(clip.fps)
	_loop_check.set_pressed_no_signal(clip.loop)
	_flip_h_check.set_pressed_no_signal(clip.flip_h)
	_flip_v_check.set_pressed_no_signal(clip.flip_v)
	_refresh_frame_list()
	if not clip.frames.is_empty():
		_region.region = clip.frames[0]


func _add_clip() -> void:
	if target == null:
		return
	var clip_name := _clip_name_edit.text.strip_edges()
	if clip_name.is_empty() or target.has_animation(StringName(clip_name)):
		return
	var clip: AnimationClip = AnimationClipScript.new()
	clip.name = clip_name
	target.clips[clip_name] = clip
	_refresh_clip_list()
	_clip_name_edit.clear()


func _rename_clip() -> void:
	if target == null or _clip_list.get_selected_items().is_empty():
		return
	var index := _clip_list.get_selected_items()[0]
	var old_name := StringName(_clip_list.get_item_text(index))
	var new_name := _clip_name_edit.text.strip_edges()
	if new_name.is_empty() or new_name == String(old_name):
		return
	if target.has_animation(StringName(new_name)):
		return
	target.clips[new_name] = target.clips[old_name]
	target.clips[new_name].name = new_name
	target.clips.erase(old_name)
	_refresh_clip_list()


func _delete_clip() -> void:
	if target == null or _clip_list.get_selected_items().is_empty():
		return
	var index := _clip_list.get_selected_items()[0]
	var clip_name := StringName(_clip_list.get_item_text(index))
	target.clips.erase(clip_name)
	_preview_clip = null
	_refresh_clip_list()


func _current_clip() -> AnimationClip:
	if target == null or _clip_list.get_selected_items().is_empty():
		return null
	var index := _clip_list.get_selected_items()[0]
	if index >= _clip_list.get_item_count():
		return null
	return target.get_clip(StringName(_clip_list.get_item_text(index)))


func _selected_frame_index() -> int:
	if _frame_list.get_selected_items().is_empty():
		return -1
	return _frame_list.get_selected_items()[0]


func _add_frame() -> void:
	var clip := _current_clip()
	if clip == null or _region.region.size.x <= 0.0 or _region.region.size.y <= 0.0:
		return
	clip.add_frame(_region.region)
	_refresh_frame_list()


func _update_frame() -> void:
	var clip := _current_clip()
	var index := _selected_frame_index()
	if clip == null or index < 0 or _region.region.size.x <= 0.0:
		return
	clip.frames[index] = _region.region
	_refresh_frame_list()


func _remove_frame() -> void:
	var clip := _current_clip()
	var index := _selected_frame_index()
	if clip == null or index < 0:
		return
	clip.remove_frame(index)
	_refresh_frame_list()


func _move_frame(offset: int) -> void:
	var clip := _current_clip()
	var index := _selected_frame_index()
	if clip == null or index < 0:
		return
	var target_index := index + offset
	if target_index < 0 or target_index >= clip.frame_count():
		return
	clip.move_frame(index, target_index)
	_refresh_frame_list()
	if target_index < _frame_list.get_item_count():
		_frame_list.select(target_index)


func _refresh_frame_list() -> void:
	_frame_list.clear()
	var clip := _current_clip()
	if clip == null:
		return
	for i in clip.frames.size():
		var rect := clip.frames[i]
		_frame_list.add_item("#%d  %dx%d  (%d, %d)" % [
			i + 1, int(rect.size.x), int(rect.size.y), int(rect.position.x), int(rect.position.y)])


func _on_frame_selected(index: int) -> void:
	var clip := _current_clip()
	if clip == null or index < 0 or index >= clip.frames.size():
		return
	_region.region = clip.frames[index]


func _start_preview() -> void:
	_preview_clip = _current_clip()
	if _preview_clip == null:
		return
	_preview_index = 0
	_preview_time = 0.0
	_preview_playing = true


func _pause_preview() -> void:
	_preview_playing = false


func _stop_preview() -> void:
	_preview_playing = false
	_preview_clip = null
	_preview_rect.texture = null
	_preview_label.text = ""


func _process(delta: float) -> void:
	if not _preview_playing:
		return
	if _preview_clip == null or _preview_clip.frames.is_empty():
		_preview_playing = false
		return
	_preview_time += delta * _preview_clip.fps
	var steps := int(_preview_time)
	if steps > 0:
		_preview_time -= float(steps)
		_preview_index += steps
		var count := _preview_clip.frame_count()
		if _preview_index >= count:
			if _preview_clip.loop:
				_preview_index = _preview_index % count
			else:
				_preview_index = count - 1
				_preview_playing = false
	_update_preview()


func _update_preview() -> void:
	if _preview_clip == null or _preview_clip.frames.is_empty():
		return
	var rect := _preview_clip.frame_rect(_preview_index)
	if target != null and target.texture != null:
		var atlas := AtlasTexture.new()
		atlas.atlas = target.texture
		atlas.region = rect
		_preview_rect.texture = atlas
	_preview_label.text = "%s  [%d/%d]  %dx%d" % [
		_preview_clip.name, _preview_index + 1, _preview_clip.frame_count(),
		int(rect.size.x), int(rect.size.y)]
