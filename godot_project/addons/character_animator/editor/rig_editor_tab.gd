@tool
extends VBoxContainer
## Dock tab for skeletal (bone) animation: build a CharacterRig on a selected
## CharacterSkeleton, author BoneClip keyframes per bone, and preview them in
## the editor viewport.

const CharacterSkeletonScript := preload("res://addons/character_animator/runtime/character_skeleton.gd")
const CharacterRigScript := preload("res://addons/character_animator/runtime/character_rig.gd")
const BoneDefScript := preload("res://addons/character_animator/runtime/bone_def.gd")
const SkeletonAnimatorScript := preload("res://addons/character_animator/runtime/skeleton_animator.gd")
const BoneClipScript := preload("res://addons/character_animator/runtime/bone_clip.gd")
const BoneTrackScript := preload("res://addons/character_animator/runtime/bone_track.gd")
const BoneKeyScript := preload("res://addons/character_animator/runtime/bone_key.gd")
const UndoServiceScript := preload("res://addons/character_animator/editor/undo_service.gd")

var editor_interface: EditorInterface
var target: CharacterSkeleton = null

var _target_label: Label
var _create_button: Button
var _bone_name_edit: LineEdit
var _parent_option: OptionButton
var _add_bone_button: Button
var _bone_list: ItemList
var _remove_bone_button: Button
var _rest_x: SpinBox
var _rest_y: SpinBox
var _rest_rot: SpinBox
var _rest_scale_x: SpinBox
var _rest_scale_y: SpinBox
var _apply_rest_button: Button
var _clip_name_edit: LineEdit
var _add_clip_button: Button
var _clip_list: ItemList
var _remove_clip_button: Button
var _time_spin: SpinBox
var _key_x: SpinBox
var _key_y: SpinBox
var _key_rot: SpinBox
var _key_scale_x: SpinBox
var _key_scale_y: SpinBox
var _add_key_button: Button
var _delete_key_button: Button
var _key_list: ItemList
var _play_button: Button
var _stop_button: Button

var _preview_clip: BoneClip = null
var _preview_time := 0.0
var _preview_playing := false


func _ready() -> void:
	_build_ui()
	_sync_target()


func refresh_target() -> void:
	target = _find_target()
	_sync_target()


func _build_ui() -> void:
	_target_label = Label.new()
	_target_label.text = "No CharacterSkeleton selected"
	add_child(_target_label)

	_create_button = Button.new()
	_create_button.text = "Create CharacterSkeleton on selection"
	_create_button.pressed.connect(_create_skeleton)
	add_child(_create_button)

	add_child(_sep())
	var bones_label := Label.new()
	bones_label.text = "Bones"
	add_child(bones_label)

	var bone_row := HBoxContainer.new()
	_bone_name_edit = LineEdit.new()
	_bone_name_edit.placeholder_text = "bone name"
	_parent_option = OptionButton.new()
	_parent_option.add_item("(root)")
	_add_bone_button = Button.new()
	_add_bone_button.text = "Add Bone"
	_add_bone_button.pressed.connect(_add_bone)
	bone_row.add_child(_bone_name_edit)
	bone_row.add_child(_parent_option)
	bone_row.add_child(_add_bone_button)
	add_child(bone_row)

	_bone_list = ItemList.new()
	_bone_list.custom_minimum_size = Vector2(0, 80)
	_bone_list.item_selected.connect(func(_i: int): _refresh_rest_fields())
	add_child(_bone_list)

	_remove_bone_button = Button.new()
	_remove_bone_button.text = "Remove Selected Bone"
	_remove_bone_button.pressed.connect(_remove_bone)
	add_child(_remove_bone_button)

	add_child(_sep())
	var rest_label := Label.new()
	rest_label.text = "Rest pose of selected bone"
	add_child(rest_label)

	var rest_grid := GridContainer.new()
	rest_grid.columns = 2
	_rest_x = _spin(-9999.0, 9999.0, 0.0, 1.0)
	_rest_y = _spin(-9999.0, 9999.0, 0.0, 1.0)
	_rest_rot = _spin(-180.0, 180.0, 0.0, 0.5)
	_rest_scale_x = _spin(0.01, 100.0, 1.0, 0.1)
	_rest_scale_y = _spin(0.01, 100.0, 1.0, 0.1)
	_add_pair(rest_grid, "Pos X", _rest_x)
	_add_pair(rest_grid, "Pos Y", _rest_y)
	_add_pair(rest_grid, "Rotation (deg)", _rest_rot)
	_add_pair(rest_grid, "Scale X", _rest_scale_x)
	_add_pair(rest_grid, "Scale Y", _rest_scale_y)
	add_child(rest_grid)

	_apply_rest_button = Button.new()
	_apply_rest_button.text = "Apply Rest Pose"
	_apply_rest_button.pressed.connect(_apply_rest)
	add_child(_apply_rest_button)

	add_child(_sep())
	var clips_label := Label.new()
	clips_label.text = "Bone clips (SkeletonAnimator)"
	add_child(clips_label)

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
	_clip_list.custom_minimum_size = Vector2(0, 60)
	_clip_list.item_selected.connect(func(_i: int): _refresh_key_list())
	add_child(_clip_list)

	_remove_clip_button = Button.new()
	_remove_clip_button.text = "Remove Selected Clip"
	_remove_clip_button.pressed.connect(_remove_clip)
	add_child(_remove_clip_button)

	add_child(_sep())
	var keys_label := Label.new()
	keys_label.text = "Keyframe for selected bone in selected clip"
	add_child(keys_label)

	var key_grid := GridContainer.new()
	key_grid.columns = 2
	_time_spin = _spin(0.0, 60.0, 0.0, 0.05)
	_time_spin.suffix = " s"
	_key_x = _spin(-9999.0, 9999.0, 0.0, 0.5)
	_key_y = _spin(-9999.0, 9999.0, 0.0, 0.5)
	_key_rot = _spin(-360.0, 360.0, 0.0, 1.0)
	_key_scale_x = _spin(-100.0, 100.0, 1.0, 0.1)
	_key_scale_y = _spin(-100.0, 100.0, 1.0, 0.1)
	_add_pair(key_grid, "Time", _time_spin)
	_add_pair(key_grid, "Pos X", _key_x)
	_add_pair(key_grid, "Pos Y", _key_y)
	_add_pair(key_grid, "Rotation (deg)", _key_rot)
	_add_pair(key_grid, "Scale X", _key_scale_x)
	_add_pair(key_grid, "Scale Y", _key_scale_y)
	add_child(key_grid)

	var key_row := HBoxContainer.new()
	_add_key_button = Button.new()
	_add_key_button.text = "Add / Update Key"
	_add_key_button.pressed.connect(_add_key)
	_delete_key_button = Button.new()
	_delete_key_button.text = "Delete Key"
	_delete_key_button.pressed.connect(_delete_key)
	key_row.add_child(_add_key_button)
	key_row.add_child(_delete_key_button)
	add_child(key_row)

	_key_list = ItemList.new()
	_key_list.custom_minimum_size = Vector2(0, 60)
	_key_list.item_selected.connect(_on_key_selected)
	add_child(_key_list)

	add_child(_sep())
	var preview_row := HBoxContainer.new()
	_play_button = Button.new()
	_play_button.text = "Preview Clip"
	_play_button.pressed.connect(_start_preview)
	_stop_button = Button.new()
	_stop_button.text = "Stop"
	_stop_button.pressed.connect(_stop_preview)
	preview_row.add_child(_play_button)
	preview_row.add_child(_stop_button)
	add_child(preview_row)


func _sep() -> HSeparator:
	var sep := HSeparator.new()
	sep.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return sep


func _spin(min_value: float, max_value: float, value: float, step: float) -> SpinBox:
	var spin := SpinBox.new()
	spin.min_value = min_value
	spin.max_value = max_value
	spin.step = step
	spin.value = value
	return spin


func _add_pair(grid: GridContainer, label_text: String, spin: SpinBox) -> void:
	var label := Label.new()
	label.text = label_text
	grid.add_child(label)
	grid.add_child(spin)


func _find_target() -> CharacterSkeleton:
	if editor_interface == null:
		return null
	for node in editor_interface.get_selection().get_selected_nodes():
		if node is CharacterSkeleton:
			return node
	return null


func _create_skeleton() -> void:
	if editor_interface == null:
		return
	var root := editor_interface.get_edited_scene_root()
	if root == null:
		return
	var parent: Node = root
	var selection := editor_interface.get_selection().get_selected_nodes()
	if not selection.is_empty():
		parent = selection[0]
	var node := Node2D.new()
	node.name = "CharacterSkeleton"
	node.set_script(CharacterSkeletonScript)
	var undo := UndoServiceScript.new(editor_interface)
	undo.add_node(parent, node, root)
	editor_interface.get_selection().clear()
	editor_interface.get_selection().add_node(node)
	target = node
	_sync_target()


func _ensure_rig() -> CharacterRig:
	if target.rig == null:
		target.rig = CharacterRigScript.new()
	return target.rig


func _ensure_animator() -> SkeletonAnimator:
	for child in target.get_children():
		if child is SkeletonAnimator:
			return child
	var animator := Node.new()
	animator.name = "SkeletonAnimator"
	animator.set_script(SkeletonAnimatorScript)
	target.add_child(animator)
	animator.owner = target.owner
	return animator


func _sync_target() -> void:
	if target == null:
		_target_label.text = "No CharacterSkeleton selected"
		return
	_target_label.text = "Target: %s" % target.name
	_refresh_bone_list()
	_refresh_clip_list()


func _refresh_bone_list() -> void:
	_bone_list.clear()
	var previous := _parent_option.get_selected()
	_parent_option.clear()
	_parent_option.add_item("(root)")
	if target == null or target.rig == null:
		return
	for bone in target.rig.bones:
		_bone_list.add_item(String(bone.bone_name))
		_parent_option.add_item(String(bone.bone_name))
	if previous >= 0 and previous < _parent_option.get_item_count():
		_parent_option.select(previous)
	_refresh_rest_fields()


func _selected_bone_index() -> int:
	if _bone_list.get_selected_items().is_empty():
		return -1
	return _bone_list.get_selected_items()[0]


func _selected_bone() -> BoneDef:
	if target == null or target.rig == null:
		return null
	var index := _selected_bone_index()
	if index < 0 or index >= target.rig.bones.size():
		return null
	return target.rig.bones[index]


func _add_bone() -> void:
	_ensure_rig()
	if target.rig == null:
		return
	var bone_name := _bone_name_edit.text.strip_edges()
	if bone_name.is_empty() or target.rig.has_bone(StringName(bone_name)):
		return
	var bone: BoneDef = BoneDefScript.new()
	bone.bone_name = bone_name
	if _parent_option.get_selected() > 0:
		bone.parent_bone = StringName(_parent_option.get_item_text(_parent_option.get_selected()))
	target.rig.add_bone(bone)
	if target.has_method("build_from_rig"):
		target.build_from_rig(target.rig)
	_refresh_bone_list()
	_bone_name_edit.clear()


func _remove_bone() -> void:
	if target == null or target.rig == null:
		return
	var index := _selected_bone_index()
	if index < 0:
		return
	target.rig.remove_bone(target.rig.bones[index].bone_name)
	if target.has_method("build_from_rig"):
		target.build_from_rig(target.rig)
	_refresh_bone_list()


func _refresh_rest_fields() -> void:
	var bone := _selected_bone()
	if bone == null:
		return
	_rest_x.set_value_no_signal(bone.rest_position.x)
	_rest_y.set_value_no_signal(bone.rest_position.y)
	_rest_rot.set_value_no_signal(rad_to_deg(bone.rest_rotation))
	_rest_scale_x.set_value_no_signal(bone.rest_scale.x)
	_rest_scale_y.set_value_no_signal(bone.rest_scale.y)


func _apply_rest() -> void:
	var bone := _selected_bone()
	if bone == null:
		return
	bone.rest_position = Vector2(_rest_x.value, _rest_y.value)
	bone.rest_rotation = deg_to_rad(_rest_rot.value)
	bone.rest_scale = Vector2(_rest_scale_x.value, _rest_scale_y.value)
	if target.has_method("build_from_rig"):
		target.build_from_rig(target.rig)


func _refresh_clip_list() -> void:
	_clip_list.clear()
	var animator := _ensure_animator()
	for clip_name in animator.clips:
		_clip_list.add_item(String(clip_name))
	if _clip_list.get_item_count() > 0:
		_clip_list.select(0)
		_refresh_key_list()


func _selected_clip() -> BoneClip:
	var animator := _ensure_animator()
	if _clip_list.get_selected_items().is_empty():
		return null
	var index := _clip_list.get_selected_items()[0]
	if index >= _clip_list.get_item_count():
		return null
	return animator.get_clip(StringName(_clip_list.get_item_text(index)))


func _add_clip() -> void:
	var animator := _ensure_animator()
	var clip_name := _clip_name_edit.text.strip_edges()
	if clip_name.is_empty() or animator.has_clip(StringName(clip_name)):
		return
	var clip: BoneClip = BoneClipScript.new()
	clip.name = clip_name
	animator.clips[clip_name] = clip
	_refresh_clip_list()
	_clip_name_edit.clear()


func _remove_clip() -> void:
	var animator := _ensure_animator()
	if _clip_list.get_selected_items().is_empty():
		return
	var index := _clip_list.get_selected_items()[0]
	animator.clips.erase(StringName(_clip_list.get_item_text(index)))
	_preview_clip = null
	_refresh_clip_list()


func _selected_track() -> BoneTrack:
	var bone := _selected_bone()
	var clip := _selected_clip()
	if bone == null or clip == null:
		return null
	return clip.ensure_track(bone.bone_name)


func _refresh_key_list() -> void:
	_key_list.clear()
	var track := _selected_track()
	if track == null:
		return
	for i in track.keys.size():
		var key := track.keys[i]
		_key_list.add_item("t=%.2f  pos(%.0f, %.0f)  rot %.0f  scl(%.2f, %.2f)" % [
			key.time, key.position.x, key.position.y, rad_to_deg(key.rotation),
			key.scale.x, key.scale.y])


func _on_key_selected(index: int) -> void:
	var track := _selected_track()
	if track == null or index < 0 or index >= track.keys.size():
		return
	var key := track.keys[index]
	_time_spin.set_value_no_signal(key.time)
	_key_x.set_value_no_signal(key.position.x)
	_key_y.set_value_no_signal(key.position.y)
	_key_rot.set_value_no_signal(rad_to_deg(key.rotation))
	_key_scale_x.set_value_no_signal(key.scale.x)
	_key_scale_y.set_value_no_signal(key.scale.y)


func _add_key() -> void:
	var track := _selected_track()
	if track == null:
		return
	var key: BoneKey = BoneKeyScript.new()
	key.time = _time_spin.value
	key.position = Vector2(_key_x.value, _key_y.value)
	key.rotation = deg_to_rad(_key_rot.value)
	key.scale = Vector2(_key_scale_x.value, _key_scale_y.value)
	track.set_key(key)
	_refresh_key_list()


func _delete_key() -> void:
	var track := _selected_track()
	if track == null or _key_list.get_selected_items().is_empty():
		return
	var index := _key_list.get_selected_items()[0]
	if index < 0 or index >= track.keys.size():
		return
	track.remove_key_at(index)
	_refresh_key_list()


func _start_preview() -> void:
	_preview_clip = _selected_clip()
	if _preview_clip == null:
		return
	_preview_time = 0.0
	_preview_playing = true


func _stop_preview() -> void:
	_preview_playing = false
	_preview_clip = null
	if target != null and target.has_method("reset_to_rest"):
		target.reset_to_rest()


func _process(delta: float) -> void:
	if not _preview_playing or target == null:
		return
	if _preview_clip == null:
		return
	var duration := _preview_clip.duration()
	if duration <= 0.0:
		return
	_preview_time += delta
	if _preview_time > duration:
		if _preview_clip.loop:
			_preview_time = fmod(_preview_time, duration)
		else:
			_preview_time = duration
			_preview_playing = false
	_apply_clip_at(_preview_clip, _preview_time)


func _apply_clip_at(clip: BoneClip, time: float) -> void:
	var out := {}
	clip.sample(time, out)
	for bone_name in out:
		var key: BoneKey = out[bone_name]
		target.apply_pose(bone_name, key.position, key.rotation, key.scale)
