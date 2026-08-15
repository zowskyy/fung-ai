class_name ValidationResult
extends RefCounted

## Represents the result of a JSON Schema validation operation.
## Contains success status, collected errors, and JSON path information.

var success: bool = true
var errors: Array[String] = []
var path: String = ""


## Add a validation error with optional path information.
func add_error(message: String, error_path: String = "") -> void:
	success = false
	var full_message := message
	if error_path:
		full_message = "%s (at path: %s)" % [message, error_path]
	else:
		full_message = message
	errors.append(full_message)


## Serialize the validation result to a dictionary for logging/debugging.
func to_dict() -> Dictionary:
	return {
		"success": success,
		"error_count": errors.size(),
		"errors": errors,
		"path": path,
	}
