@tool
class_name WaitBeatRunner
extends BeatRunner

var _b: WaitBeat
var _timeout: Timer


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as WaitBeat


func start() -> void:
	if _b.duration_seconds <= 0.0:
		completed.emit()
		return
	_timeout = _timeout_timer(_b.duration_seconds)
	_timeout.timeout.connect(_on_timeout)
	_timeout.start()


func _on_timeout() -> void:
	completed.emit()
