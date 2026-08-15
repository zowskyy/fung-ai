@tool
extends EditorPlugin

## Editor integration for the Scene Animator add-on. Registers the authoring
## dock and the ScenePlan inspector hook, and removes both on deactivation.
## All add/remove paths are idempotent so reloads cannot register twice.

const DOCK_SCRIPT := "res://addons/scene_animator/editor/scene_plan_dock.gd"
const INSPECTOR_SCRIPT := "res://addons/scene_animator/editor/inspectors/scene_plan_inspector.gd"

var _dock: Control
var _inspector: EditorInspectorPlugin


func _enter_tree() -> void:
	_add_dock()
	_add_inspector()


func _exit_tree() -> void:
	_remove_inspector()
	_remove_dock()


func _add_dock() -> void:
	if _dock != null:
		return
	var script := load(DOCK_SCRIPT)
	if script == null:
		push_error("Scene Animator: dock script failed to load: " + DOCK_SCRIPT)
		return
	_dock = script.new()
	_dock.name = &"SceneAnimatorDock"
	add_control_to_dock(EditorPlugin.DOCK_SLOT_LEFT_BR, _dock)


func _remove_dock() -> void:
	if _dock == null:
		return
	remove_control_from_docks(_dock)
	_dock.queue_free()
	_dock = null


func _add_inspector() -> void:
	if _inspector != null:
		return
	var script := load(INSPECTOR_SCRIPT)
	if script == null:
		push_error("Scene Animator: inspector script failed to load: " + INSPECTOR_SCRIPT)
		return
	_inspector = script.new()
	add_inspector_plugin(_inspector)


func _remove_inspector() -> void:
	if _inspector == null:
		return
	remove_inspector_plugin(_inspector)
	_inspector = null
