@tool
class_name CameraBeatRunner
extends BeatRunner

var _b: CameraBeat
var _timeout: Timer
var _done := false


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as CameraBeat


func start() -> void:
	var adapter := _bindings.camera_adapter
	if adapter == null:
		failed.emit(&"missing_camera_adapter", {"beat_id": _b.beat_id})
		return

	var focus_node: Node3D = null
	if not _b.focus_target_path.is_empty():
		focus_node = _bindings.get_node(_b.focus_target_path) as Node3D

	adapter.camera_transitioned.connect(_on_transitioned, CONNECT_ONE_SHOT)
	adapter.camera_failed.connect(_on_failed, CONNECT_ONE_SHOT)
	adapter.request_mode(_b.camera_mode_id, focus_node, _b.blend_seconds)

	_timeout = _timeout_timer(_b.blend_seconds + 3.0)
	_timeout.timeout.connect(_on_timeout)
	_timeout.start()


func _on_transitioned(_mode: StringName) -> void:
	if _done:
		return
	_done = true
	completed.emit()


func _on_failed(_mode: StringName, reason: StringName) -> void:
	if _done:
		return
	_done = true
	failed.emit(reason, {"beat_id": _b.beat_id, "camera_mode_id": _b.camera_mode_id})


func _on_timeout() -> void:
	if _done:
		return
	_done = true
	failed.emit(&"camera_timeout", {
		"beat_id": _b.beat_id,
		"camera_mode_id": _b.camera_mode_id,
		"timeout_seconds": _b.blend_seconds + 3.0,
	})
