class_name SceneAnimatorTestResult
extends RefCounted

## Serializable, runner-independent record of one test suite run. The master
## runner aggregates these into the single SCENE_ANIMATOR_RESULT JSON line.

var suite_name: StringName
var passed := true
var assertions := 0
var failures: Array[Dictionary] = []
var duration_ms := 0


func fail(id: StringName, message: String, details: Dictionary = {}) -> void:
	passed = false
	failures.append({
		"id": id,
		"message": message,
		"details": details.duplicate(true),
	})


func to_dictionary() -> Dictionary:
	return {
		"suite": suite_name,
		"passed": passed,
		"assertions": assertions,
		"failures": failures,
		"duration_ms": duration_ms,
	}
