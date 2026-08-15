@tool
class_name ScenePlanDock
extends PanelContainer

## Authoring dock. Loads a ScenePlan resource, summarizes it, lists its actors
## and beats, and runs the ScenePlanValidator. The dock is built from plain
## Controls in code so it works identically in the editor and headless tests.

const VALIDATOR_SCRIPT := "res://addons/scene_animator/editor/validators/scene_plan_validator.gd"

var _plan: ScenePlan
var _registry: SceneCapabilityRegistry

var _summary_label: Label
var _beats_tree: Tree
var _issues_label: Label
var _path_edit: LineEdit
var _validate_button: Button


func _ready() -> void:
	_build_ui()
	_refresh()


func current_plan() -> ScenePlan:
	return _plan


func set_capability_registry(registry: SceneCapabilityRegistry) -> void:
	_registry = registry
	_refresh()


func set_plan(plan: ScenePlan) -> void:
	_plan = plan
	if plan != null and plan.resource_path != "":
		_path_edit.text = plan.resource_path
	_refresh()


func load_plan(path: String) -> bool:
	var trimmed := path.strip_edges()
	if trimmed == "":
		return false
	var res := load(trimmed)
	if res is ScenePlan:
		set_plan(res)
		return true
	push_error("Scene Animator: not a ScenePlan resource: " + trimmed)
	return false


func validate_current() -> ScenePlanValidationResult:
	if _plan == null:
		return null
	var Validator := load(VALIDATOR_SCRIPT)
	var result: ScenePlanValidationResult = Validator.validate(_plan, _registry)
	_render_issues(result)
	return result


# --------------------------------------------------------------------------- #
# UI construction
# --------------------------------------------------------------------------- #

func _build_ui() -> void:
	var root := VBoxContainer.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(root)

	var heading := Label.new()
	heading.text = "Scene Animator"
	heading.add_theme_font_size_override(&"font_size", 16)
	root.add_child(heading)

	var path_row := HBoxContainer.new()
	_path_edit = LineEdit.new()
	_path_edit.placeholder_text = "res://scenes/plans/plan.tres"
	_path_edit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var load_button := Button.new()
	load_button.text = "Load"
	load_button.pressed.connect(_on_load_pressed)
	path_row.add_child(_path_edit)
	path_row.add_child(load_button)
	root.add_child(path_row)

	_summary_label = Label.new()
	_summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(_summary_label)

	_beats_tree = Tree.new()
	_beats_tree.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(_beats_tree)

	var validate_row := HBoxContainer.new()
	_validate_button = Button.new()
	_validate_button.text = "Validate"
	_validate_button.pressed.connect(_on_validate_pressed)
	validate_row.add_child(_validate_button)
	root.add_child(validate_row)

	_issues_label = Label.new()
	_issues_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	root.add_child(_issues_label)


# --------------------------------------------------------------------------- #
# Display
# --------------------------------------------------------------------------- #

func _refresh() -> void:
	if _plan == null:
		_summary_label.text = "No plan loaded."
		_beats_tree.clear()
		_issues_label.text = ""
		return
	_summary_label.text = "%s\nid: %s\nactors: %d, beats: %d, capabilities: %s" % [
		_plan.display_name if _plan.display_name != "" else "(untitled)",
		_plan.plan_id,
		_plan.actors.size(),
		_plan.beats.size(),
		"set" if _registry != null else "none",
	]
	_build_tree()


func _build_tree() -> void:
	_beats_tree.clear()
	var root := _beats_tree.create_item()
	root.set_text(0, "Plan: " + String(_plan.plan_id))

	var actors_node := _beats_tree.create_item(root)
	actors_node.set_text(0, "Actors (%d)" % _plan.actors.size())
	for actor: SceneActorBinding in _plan.actors:
		if actor == null:
			continue
		var item := _beats_tree.create_item(actors_node)
		item.set_text(0, "%s -> %s" % [actor.actor_id, actor.actor_path])

	var beats_node := _beats_tree.create_item(root)
	beats_node.set_text(0, "Beats (%d)" % _plan.beats.size())
	for beat: SceneBeat in _plan.beats:
		if beat == null:
			continue
		var item := _beats_tree.create_item(beats_node)
		var enabled_mark := "" if beat.enabled else " (disabled)"
		item.set_text(0, "%s [%s]%s" % [beat.beat_id, beat.beat_type(), enabled_mark])


func _render_issues(result: ScenePlanValidationResult) -> void:
	var lines: Array[String] = []
	for issue: ScenePlanValidationIssue in result.issues:
		var where := ""
		if issue.beat_id != &"":
			where = " beat=" + String(issue.beat_id)
		elif issue.actor_id != &"":
			where = " actor=" + String(issue.actor_id)
		var severity := "ERROR" if issue.is_error() else ("WARN" if issue.is_warning() else "INFO")
		lines.append("[%s] %s%s - %s" % [severity, issue.code, where, issue.message])
	_issues_label.text = "\n".join(lines)


# --------------------------------------------------------------------------- #
# Handlers
# --------------------------------------------------------------------------- #

func _on_load_pressed() -> void:
	load_plan(_path_edit.text)


func _on_validate_pressed() -> void:
	validate_current()
