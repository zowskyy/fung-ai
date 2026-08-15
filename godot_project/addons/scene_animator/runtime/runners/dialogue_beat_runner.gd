@tool
class_name DialogueBeatRunner
extends BeatRunner

var _b: DialogueBeat
var _timeout: Timer
var _speaker: SceneActorAdapter
var _done := false


func setup(beat: SceneBeat, bindings: SceneBindings, registry: SceneCapabilityRegistry) -> void:
	super.setup(beat, bindings, registry)
	_b = beat as DialogueBeat


func start() -> void:
	if _b.dialogue_id == &"":
		completed.emit()
		return

	var speaker := _bindings.get_actor(_b.speaker_actor_id)
	if speaker == null:
		failed.emit(
			&"scene_animator.missing_speaker_actor",
			{
				"beat_id": _b.beat_id,
				"speaker_actor_id": _b.speaker_actor_id,
				"target_actor_id": _b.target_actor_id,
			}
		)
		return

	var target_actor: SceneActorAdapter = null
	if not _b.target_actor_id.is_empty():
		target_actor = _bindings.get_actor(_b.target_actor_id)
		if target_actor == null:
			failed.emit(
				&"scene_animator.missing_target_actor",
				{
					"beat_id": _b.beat_id,
					"speaker_actor_id": _b.speaker_actor_id,
					"target_actor_id": _b.target_actor_id,
				}
			)
			return

	_speaker = speaker
	_speaker.action_event_emitted.connect(_on_event)

	var mech := _bindings.mechanics_registry
	if mech != null and mech.has_effect(_b.dialogue_id):
		mech.play_effect(_b.dialogue_id, {
			"scene_beat_id": _b.beat_id,
			"speaker": speaker,
			"target_actor": target_actor,
		})
		_timeout = _timeout_timer(_b.timeout_seconds)
		_timeout.timeout.connect(_on_timeout)
		_timeout.start()
	else:
		call_deferred("emit_signal", "completed")


func _on_event(event_name: StringName, _payload: Variant) -> void:
	if _done:
		return
	if event_name == &"dialogue_finished" or event_name == _b.dialogue_id:
		_done = true
		if _speaker != null and _speaker.is_connected(&"action_event_emitted", Callable(self, "_on_event")):
			_speaker.disconnect(&"action_event_emitted", Callable(self, "_on_event"))
		completed.emit()


func _on_timeout() -> void:
	if _done:
		return
	_done = true
	failed.emit(&"dialogue_timeout", {
		"beat_id": _b.beat_id,
		"dialogue_id": _b.dialogue_id,
		"timeout_seconds": _b.timeout_seconds,
	})
