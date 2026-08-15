@tool
class_name ValidationIssue
extends RefCounted
## A single structured validation result. Severity drives how the dock
## displays it; fix_id lets the dock offer a concrete Fix action later.

enum Severity { INFO, WARNING, ERROR }

var severity: Severity = Severity.INFO
var message: String = ""
var node_path: NodePath = NodePath()
var fix_id: StringName = &""


static func make(
	p_severity: Severity,
	p_message: String,
	p_node_path: NodePath = NodePath(),
	p_fix_id: StringName = &"",
) -> ValidationIssue:
	var issue := ValidationIssue.new()
	issue.severity = p_severity
	issue.message = p_message
	issue.node_path = p_node_path
	issue.fix_id = p_fix_id
	return issue


func severity_label() -> String:
	match severity:
		Severity.ERROR:
			return "ERROR"
		Severity.WARNING:
			return "WARN"
	return "INFO"
