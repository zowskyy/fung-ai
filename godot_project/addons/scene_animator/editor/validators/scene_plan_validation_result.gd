@tool
class_name ScenePlanValidationResult
extends RefCounted

## Aggregated outcome of validating one ScenePlan. Serializes to a dictionary
## for the dock readout and the headless test runner.

var plan_id: StringName
var issues: Array[ScenePlanValidationIssue] = []


func _init(p_plan_id: StringName = &"") -> void:
	plan_id = p_plan_id


func error_count() -> int:
	var n := 0
	for issue in issues:
		if issue.is_error():
			n += 1
	return n


func warning_count() -> int:
	var n := 0
	for issue in issues:
		if issue.is_warning():
			n += 1
	return n


func info_count() -> int:
	var n := 0
	for issue in issues:
		if issue.severity == ScenePlanValidationIssue.Severity.INFO:
			n += 1
	return n


func is_valid() -> bool:
	return error_count() == 0


func issue_codes() -> Array[StringName]:
	var out: Array[StringName] = []
	for issue in issues:
		out.append(issue.code)
	return out


func to_dictionary() -> Dictionary:
	var serialized: Array[Dictionary] = []
	for issue in issues:
		serialized.append(issue.to_dictionary())
	return {
		"plan_id": plan_id,
		"valid": is_valid(),
		"errors": error_count(),
		"warnings": warning_count(),
		"issues": serialized,
	}
