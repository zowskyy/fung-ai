@tool
class_name WaitForEventBeatRunner
extends BeatRunner

var _b: WaitForEventBeat
var _timeout: Timer
var _done := false
var _actor: SceneActorAdapter


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as WaitForEventBeat


func start() -> void:
	var actor := _bindings.get_actor(_b.source_actor_id)
	if actor == null:
		failed.emit(&"missing_actor", {"beat_id": _b.beat_id, "actor_id": _b.source_actor_id})
		return
	_actor = actor
	actor.action_event_emitted.connect(_on_event)
	_timeout = _timeout_timer(_b.timeout_seconds)
	_timeout.timeout.connect(_on_timeout)
	_timeout.start()


func _on_event(event_name: StringName, _payload: Variant) -> void:
	if _done:
		return
	if event_name == _b.event_name:
		_done = true
		if _actor.is_connected(&"action_event_emitted", Callable(self, "_on_event")):
			_actor.disconnect(&"action_event_emitted", Callable(self, "_on_event"))
		completed.emit()


func _on_timeout() -> void:
	if _done:
		return
	_done = true
	failed.emit(&"wait_event_timeout", {
		"beat_id": _b.beat_id,
		"source_actor_id": _b.source_actor_id,
		"event_name": _b.event_name,
		"timeout_seconds": _b.timeout_seconds,
	})
