@tool
extends EditorPlugin
## Entry point for the 2D Character Animator plugin.
##
## Registers the runtime node types as custom Godot classes, installs the
## editor dock (left edge), a profile inspector, and a Tools-menu shortcut.

const DockScene := preload("res://addons/character_animator/ui/character_animator_dock.tscn")
const InspectorScript := preload("res://addons/character_animator/editor/inspectors/character_animation_profile_inspector.gd")
const CharacterAnimator := preload("res://addons/character_animator/runtime/character_animator.gd")
const CharacterAnimationDriver := preload("res://addons/character_animator/runtime/character_animation_driver.gd")
const CharacterSkeleton := preload("res://addons/character_animator/runtime/character_skeleton.gd")
const SkeletonAnimator := preload("res://addons/character_animator/runtime/skeleton_animator.gd")

const TOOL_MENU_ITEM := "Character Animator: Open Setup"

var _dock: Control = null
var _inspector: EditorInspectorPlugin = null


func _enter_tree() -> void:
	add_custom_type("CharacterAnimator", "Sprite2D", CharacterAnimator, null)
	add_custom_type("CharacterAnimationDriver", "Node", CharacterAnimationDriver, null)
	add_custom_type("CharacterSkeleton", "Node2D", CharacterSkeleton, null)
	add_custom_type("SkeletonAnimator", "Node", SkeletonAnimator, null)

	_dock = DockScene.instantiate()
	add_control_to_dock(EditorPlugin.DOCK_SLOT_LEFT_UR, _dock)

	_inspector = InspectorScript.new()
	_inspector.set_open_callback(_open_profile_in_dock)
	add_inspector_plugin(_inspector)

	var editor := get_editor_interface()
	if editor != null and _dock != null and _dock.has_method("setup"):
		_dock.setup(editor)

	add_tool_menu_item(TOOL_MENU_ITEM, _open_setup_tab)


func _exit_tree() -> void:
	remove_tool_menu_item(TOOL_MENU_ITEM)

	if _inspector != null:
		remove_inspector_plugin(_inspector)
		_inspector = null

	if _dock != null:
		remove_control_from_docks(_dock)
		_dock.queue_free()
		_dock = null

	remove_custom_type("CharacterAnimator")
	remove_custom_type("CharacterAnimationDriver")
	remove_custom_type("CharacterSkeleton")
	remove_custom_type("SkeletonAnimator")


func _open_profile_in_dock(profile: CharacterAnimationProfile) -> void:
	if _dock != null and _dock.has_method("focus_profile"):
		_dock.focus_profile(profile)


func _open_setup_tab() -> void:
	if _dock != null and _dock.has_method("focus_setup"):
		_dock.focus_setup()
