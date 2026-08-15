class_name FakeCameraAdapter
extends SceneCameraAdapter

## Recording camera adapter. Captures request arguments and order and can emit
## a failure signal for controlled-failure tests.

var request_calls: Array[Dictionary] = []
var cancel_calls := 0
var fail_transitions := false


func request_mode(mode_id: StringName, focus_target_node: Node3D, blend_seconds: float) -> void:
	request_calls.append({
		"mode_id": mode_id,
		"focus_target": focus_target_node,
		"blend_seconds": blend_seconds,
	})
	if fail_transitions:
		camera_failed.emit(mode_id, &"fake_camera_failure")
	else:
		camera_transitioned.emit(mode_id)


func cancel() -> void:
	cancel_calls += 1
	camera_transitioned.emit(&"")
