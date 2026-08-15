@tool
class_name ScenePlanInspector
extends EditorInspectorPlugin

## Inspector hook for ScenePlan resources. Adds a one-click validation action
## that runs the ScenePlanValidator and surfaces ERROR/WARNING lines in the
## editor log. Registered by plugin.gd only under the editor process.

const VALIDATOR_SCRIPT := "res://addons/scene_animator/editor/validators/scene_plan_validator.gd"


func _can_handle(object: Object) -> bool:
	return object is ScenePlan


func _parse_begin(object: Object) -> void:
	var plan := object as ScenePlan
	var panel := VBoxContainer.new()
	var button := Button.new()
	button.text = "Validate Scene Plan"
	button.pressed.connect(_on_validate.bind(plan))
	panel.add_child(button)
	add_custom_control(panel)


func _on_validate(plan: ScenePlan) -> void:
	var Validator := load(VALIDATOR_SCRIPT)
	var result: ScenePlanValidationResult = Validator.validate(plan)
	for issue: ScenePlanValidationIssue in result.issues:
		var where := ""
		if issue.beat_id != &"":
			where = " beat=" + String(issue.beat_id)
		elif issue.actor_id != &"":
			where = " actor=" + String(issue.actor_id)
		var line := "Scene Animator validation: [%s]%s - %s" % [issue.code, where, issue.message]
		if issue.is_error():
			push_error(line)
		elif issue.is_warning():
			push_warning(line)
	if result.is_valid():
		print("Scene Animator validation: plan is valid (%d errors, %d warnings)." % [result.error_count(), result.warning_count()])
