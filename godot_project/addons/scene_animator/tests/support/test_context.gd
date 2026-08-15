class_name SceneAnimatorTestContext
extends RefCounted

## Per-suite assertion helper. Owns assertion counting and test-local
## diagnostics only; it never terminates the process.

var result: SceneAnimatorTestResult


func _init(result: SceneAnimatorTestResult) -> void:
	self.result = result


func is_true(condition: bool, id: StringName, message: String, details := {}) -> bool:
	result.assertions += 1
	if condition:
		return true
	result.fail(id, message, details)
	return false


func equals(actual: Variant, expected: Variant, id: StringName, message: String) -> bool:
	return is_true(actual == expected, id, message, {
		"actual": actual,
		"expected": expected,
	})


func approx(actual: float, expected: float, epsilon: float, id: StringName, message: String) -> bool:
	return is_true(absf(actual - expected) <= epsilon, id, message, {
		"actual": actual,
		"expected": expected,
		"epsilon": epsilon,
	})


## Awaits a runtime signal for at most timeout_seconds. Returns structured
## diagnostics instead of crashing when the condition never fires.
func await_with_timeout(awaitable_signal: Signal, timeout_seconds: float, context: String) -> Dictionary:
	var tree := Engine.get_main_loop() as SceneTree
	var start_ms := Time.get_ticks_msec()
	var timer := tree.create_timer(timeout_seconds)
	var completed := false
	awaitable_signal.connect(func() -> void:
		completed = true
	, CONNECT_ONE_SHOT)
	await timer.timeout
	var elapsed_ms := Time.get_ticks_msec() - start_ms
	return {
		"completed": completed,
		"timed_out": not completed,
		"context": context,
		"timeout_seconds": timeout_seconds,
		"duration_ms": elapsed_ms,
	}
