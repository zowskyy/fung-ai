@tool
extends VBoxContainer
## Dock tab that acts as the setup wizard: scan the scene, configure a
## CharacterAnimationProfile, generate the AnimationTree, validate the result,
## add the runtime driver, and preview the graph from a sandbox.

const ProfileScript := preload("res://addons/character_animator/runtime/character_animation_profile.gd")
const DriverScript := preload("res://addons/character_animator/runtime/character_animation_driver.gd")
const ScannerScript := preload("res://addons/character_animator/editor/character_scene_scanner.gd")
const BuilderScript := preload("res://addons/character_animator/editor/animation_graph_builder.gd")
const ValidatorScript := preload("res://addons/character_animator/editor/animation_validator.gd")
const UndoServiceScript := preload("res://addons/character_animator/editor/undo_service.gd")

const ROLE_FIELDS: Array[String] = [
	"idle", "walk", "run", "jump", "fall", "land", "crouch_idle", "crouch_move",
]

var editor_interface: EditorInterface
var target: Node = null
var profile: CharacterAnimationProfile = null
var driver: CharacterAnimationDriver = null

var _target_label: Label
var _scan_button: Button
var _scan_results: RichTextLabel
var _create_profile_button: Button
var _role_edits: Dictionary = {}
var _walk_point: SpinBox
var _run_point: SpinBox
var _transition_time: SpinBox
var _generate_button: Button
var _validate_button: Button
var _issues: RichTextLabel
var _add_runtime_button: Button
var _preview_speed: HSlider
var _preview_grounded: CheckButton
var _preview_crouching: CheckButton
var _preview_facing: CheckButton
var _jump_button: Button
var _land_button: Button
var _attack_button: Button
var _state_label: Label
var _preview_running := false


func _ready() -> void:
	_build_ui()
	refresh_target()


func refresh_target() -> void:
	target = _find_target()
	_sync_target()


func load_profile(loaded: CharacterAnimationProfile) -> void:
	profile = loaded
	_sync_profile_fields()
	_sync_target()


func _find_target() -> Node:
	if editor_interface == null:
		return null
	var selection := editor_interface.get_selection().get_selected_nodes()
	if selection.is_empty():
		return null
	for node in selection:
		if node is CharacterBody2D or node is CharacterAnimator or node is Node2D:
			return node
	return selection[0]


func _sync_target() -> void:
	if target == null:
		_target_label.text = "Select a character node in the scene"
	else:
		_target_label.text = "Target: %s" % target.name


func _build_ui() -> void:
	_target_label = Label.new()
	_target_label.text = "Select a character node"
	add_child(_target_label)

	_scan_button = Button.new()
	_scan_button.text = "Scan Selected Scene"
	_scan_button.pressed.connect(_scan_scene)
	add_child(_scan_button)

	_scan_results = RichTextLabel.new()
	_scan_results.custom_minimum_size = Vector2(0, 90)
	_scan_results.bbcode_enabled = true
	_scan_results.scroll_following = true
	add_child(_scan_results)

	add_child(_sep())

	var profile_label := Label.new()
	profile_label.text = "CharacterAnimationProfile"
	add_child(profile_label)

	_create_profile_button = Button.new()
	_create_profile_button.text = "Create / Reset Profile"
	_create_profile_button.pressed.connect(_create_profile)
	add_child(_create_profile_button)

	var grid := GridContainer.new()
	grid.columns = 2
	for role in ROLE_FIELDS:
		var label := Label.new()
		label.text = role
		var edit := LineEdit.new()
		edit.text_changed.connect(func(_t: String): _apply_profile_from_fields())
		_role_edits[role] = edit
		grid.add_child(label)
		grid.add_child(edit)
	_walk_point = _spin(0.0, 1.0, 0.45, 0.01)
	_run_point = _spin(0.0, 1.0, 1.0, 0.01)
	_transition_time = _spin(0.0, 1.0, 0.12, 0.01)
	_add_pair(grid, "walk_point", _walk_point)
	_add_pair(grid, "run_point", _run_point)
	_add_pair(grid, "transition_blend_time", _transition_time)
	add_child(grid)

	var actions := HBoxContainer.new()
	_generate_button = Button.new()
	_generate_button.text = "Generate AnimationTree"
	_generate_button.pressed.connect(_generate)
	_validate_button = Button.new()
	_validate_button.text = "Validate"
	_validate_button.pressed.connect(_validate)
	_add_runtime_button = Button.new()
	_add_runtime_button.text = "Add Runtime Driver"
	_add_runtime_button.pressed.connect(_add_runtime)
	actions.add_child(_generate_button)
	actions.add_child(_validate_button)
	actions.add_child(_add_runtime_button)
	add_child(actions)

	_issues = RichTextLabel.new()
	_issues.custom_minimum_size = Vector2(0, 90)
	_issues.bbcode_enabled = true
	add_child(_issues)

	add_child(_sep())
	var preview_label := Label.new()
	preview_label.text = "Preview sandbox (writes AnimationTree parameters only)"
	add_child(preview_label)

	_preview_speed = HSlider.new()
	_preview_speed.min_value = 0.0
	_preview_speed.max_value = 1.0
	_preview_speed.step = 0.01
	_preview_speed.value_changed.connect(func(_v: float): _feed_preview())
	add_child(_preview_speed)

	var toggles := HBoxContainer.new()
	_preview_grounded = CheckButton.new()
	_preview_grounded.text = "Grounded"
	_preview_grounded.toggled.connect(func(_v: bool): _feed_preview())
	_preview_crouching = CheckButton.new()
	_preview_crouching.text = "Crouching"
	_preview_crouching.toggled.connect(func(_v: bool): _feed_preview())
	_preview_facing = CheckButton.new()
	_preview_facing.text = "Facing right"
	_preview_facing.button_pressed = true
	_preview_facing.toggled.connect(func(_v: bool): _feed_preview())
	toggles.add_child(_preview_grounded)
	toggles.add_child(_preview_crouching)
	toggles.add_child(_preview_facing)
	add_child(toggles)

	var state_buttons := HBoxContainer.new()
	_jump_button = Button.new()
	_jump_button.text = "Jump"
	_jump_button.pressed.connect(func(): _request_preview_state(&"Jump"))
	_land_button = Button.new()
	_land_button.text = "Land"
	_land_button.pressed.connect(func(): _request_preview_state(&"Land"))
	_attack_button = Button.new()
	_attack_button.text = "Attack"
	_attack_button.pressed.connect(func(): _request_preview_state(&"Attack1"))
	state_buttons.add_child(_jump_button)
	state_buttons.add_child(_land_button)
	state_buttons.add_child(_attack_button)
	add_child(state_buttons)

	_state_label = Label.new()
	_state_label.text = "State: -"
	add_child(_state_label)


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
	spin.value_changed.connect(func(_v: float): _apply_profile_from_fields())
	return spin


func _add_pair(grid: GridContainer, label_text: String, spin: SpinBox) -> void:
	var label := Label.new()
	label.text = label_text
	grid.add_child(label)
	grid.add_child(spin)


func _scan_scene() -> void:
	if editor_interface == null:
		return
	var root := editor_interface.get_edited_scene_root()
	if root == null:
		_scan_results.text = "No edited scene open."
		return
	var found := ScannerScript.scan(root)
	var text := "[color=#9fd7ff]Scan results:[/color]\n"
	text += "  Bodies: %d  Animators: %d  Sprites: %d  AnimatedSprites: %d\n" % [
		found["bodies"].size(), found["animators"].size(), found["sprites"].size(),
		found["animated_sprites"].size()]
	text += "  AnimationPlayers: %d  AnimationTrees: %d  Skeletons: %d  SkeletonAnimators: %d" % [
		found["players"].size(), found["trees"].size(), found["skeletons"].size(),
		found["skeleton_animators"].size()]
	_scan_results.text = text


func _create_profile() -> void:
	profile = ProfileScript.new()
	profile.animator_path = _find_animator_path()
	profile.visuals_path = _find_visuals_path()
	_sync_profile_fields()
	_issues.text = "[color=#8ae28a]New profile created (not yet saved). Use Generate to build the tree.[/color]"


func _find_animator_path() -> NodePath:
	if target == null:
		return NodePath()
	for node in [target] + target.get_children():
		if node is CharacterAnimator:
			return target.get_path_to(node)
	return NodePath()


func _find_visuals_path() -> NodePath:
	if target == null:
		return NodePath()
	for child in target.get_children():
		if child is Sprite2D or child is AnimatedSprite2D:
			return target.get_path_to(child)
	for child in target.get_children():
		if child.name == "Visuals":
			return target.get_path_to(child)
	return NodePath()


func _sync_profile_fields() -> void:
	if profile == null:
		for role in ROLE_FIELDS:
			(_role_edits[role] as LineEdit).set_text_no_signal("")
		_walk_point.set_value_no_signal(0.45)
		_run_point.set_value_no_signal(1.0)
		_transition_time.set_value_no_signal(0.12)
		return
	for role in ROLE_FIELDS:
		(_role_edits[role] as LineEdit).set_text_no_signal(String(profile.get(role)))
	_walk_point.set_value_no_signal(profile.walk_point)
	_run_point.set_value_no_signal(profile.run_point)
	_transition_time.set_value_no_signal(profile.transition_blend_time)


func _apply_profile_from_fields() -> void:
	if profile == null:
		return
	for role in ROLE_FIELDS:
		profile.set(role, StringName((_role_edits[role] as LineEdit).text.strip_edges()))
	profile.walk_point = _walk_point.value
	profile.run_point = _run_point.value
	profile.transition_blend_time = _transition_time.value


func _generate() -> void:
	if target == null or profile == null:
		_issues.text = "[color=#ff9c9c]Select a target and create a profile first.[/color]"
		return
	_apply_profile_from_fields()
	var result := BuilderScript.build(target, profile)
	var tree := result["animation_tree"] as AnimationTree
	if tree != null:
		driver = _ensure_driver()
		_issues.text = "[color=#8ae28a]Generated tree with %d animations.[/color]\n" % result["created_animations"].size()
		for warning in result["warnings"]:
			_issues.append_text("[color=#ffd27d]WARN: %s[/color]\n" % warning)
	else:
		_issues.text = "[color=#ff9c9c]Generation failed (no target or profile).[/color]"


func _validate() -> void:
	if target == null or profile == null:
		_issues.text = "[color=#ff9c9c]Select a target and create a profile first.[/color]"
		return
	_apply_profile_from_fields()
	var issues := ValidatorScript.validate(target, profile)
	_issues.text = ""
	var errors := 0
	for issue in issues:
		var color := "#ff9c9c"
		if issue.severity == ValidationIssue.Severity.WARNING:
			color = "#ffd27d"
		_issues.append_text("[color=%s]%s: %s[/color]\n" % [color, issue.severity_label(), issue.message])
		if issue.severity == ValidationIssue.Severity.ERROR:
			errors += 1
	if errors == 0:
		_issues.append_text("[color=#8ae28a]Validation finished with %d issue(s).[/color]" % issues.size())


func _add_runtime() -> void:
	if target == null:
		return
	driver = _ensure_driver()
	if profile != null and driver.profile == null:
		driver.profile = profile
	_issues.text = "[color=#8ae28a]Runtime driver ready on '%s'.[/color]" % driver.name


func _ensure_driver() -> CharacterAnimationDriver:
	for child in target.get_children():
		if child is CharacterAnimationDriver:
			var existing := child as CharacterAnimationDriver
			var tree := target.get_node_or_null("AnimationTree") as AnimationTree
			if tree != null:
				existing.animation_tree = tree
			existing.profile = profile
			return existing
	var node := Node.new()
	node.name = "CharacterAnimationDriver"
	node.set_script(DriverScript)
	var undo := UndoServiceScript.new(editor_interface)
	undo.add_node(target, node, target.owner if target.owner != null else target)
	var new_driver := node as CharacterAnimationDriver
	var tree_node := target.get_node_or_null("AnimationTree") as AnimationTree
	if tree_node != null:
		new_driver.animation_tree = tree_node
	new_driver.profile = profile
	if profile != null and profile.visuals_path != NodePath():
		var visuals_node := target.get_node_or_null(profile.visuals_path)
		if visuals_node is Node2D:
			new_driver.visuals = visuals_node
	if editor_interface != null:
		editor_interface.get_selection().clear()
		editor_interface.get_selection().add_node(node)
	return new_driver


func _feed_preview() -> void:
	if driver == null or driver.animation_tree == null:
		return
	driver.update_locomotion(
		Vector2(_preview_speed.value * 320.0, 0.0),
		_preview_grounded.button_pressed,
		_preview_crouching.button_pressed,
		_preview_facing.button_pressed,
	)
	_state_label.text = "State: %s" % driver.current_state_name()


func _request_preview_state(state: StringName) -> void:
	if driver == null or driver.animation_tree == null:
		return
	driver.request_state(state)
	_state_label.text = "State: %s" % driver.current_state_name()


func _process(delta: float) -> void:
	if _preview_running and driver != null and driver.animation_tree != null:
		driver.animation_tree.advance(delta)
		_state_label.text = "State: %s" % driver.current_state_name()
