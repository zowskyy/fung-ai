@tool
class_name ScenePlanValidationIssue
extends RefCounted

## One authored-plan problem. Severity drives the dock/inspector display and the
## valid flag: errors block playback, warnings are tolerated. Codes are stable
## so tests and CI can assert on them.

enum Severity { INFO, WARNING, ERROR }

var severity: Severity
var code: StringName
var message: String
var beat_id: StringName
var actor_id: StringName
var details: Dictionary


func _init(
	p_severity: Severity,
	p_code: StringName,
	p_message: String,
	p_beat_id: StringName = &"",
	p_actor_id: StringName = &"",
	p_details: Dictionary = {}
) -> void:
	severity = p_severity
	code = p_code
	message = p_message
	beat_id = p_beat_id
	actor_id = p_actor_id
	details = p_details.duplicate(true)


func is_error() -> bool:
	return severity == Severity.ERROR


func is_warning() -> bool:
	return severity == Severity.WARNING


func to_dictionary() -> Dictionary:
	return {
		"severity": severity,
		"code": code,
		"beat_id": beat_id,
		"actor_id": actor_id,
		"message": message,
		"details": details.duplicate(true),
	}
