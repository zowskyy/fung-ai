class_name CutsceneDirector
extends Node

signal finished(sequence_id: String)
signal beat_started(beat: Dictionary)
signal choice_requested(beat: Dictionary)

var _dialogue_runner: DialogueRunner = DialogueRunner.new()
var _choice_resolver: ChoiceResolver = ChoiceResolver.new()
var _condition_evaluator: ConditionEvaluator = ConditionEvaluator.new()

var _sequence_id: String = ""
var _beats_by_id: Dictionary = {}
var _beats_order: Array = []
var _flags: Dictionary = {}
var _skipped: bool = false
var _pending_choice_beat_id: String = ""


func play(sequence: Dictionary, flags: Dictionary = {}) -> void:
	_sequence_id = sequence.get("sequence_id", "")
	_beats_order = sequence.get("beats", [])
	_beats_by_id = {}
	for beat: Dictionary in _beats_order:
		_beats_by_id[beat.get("id", "")] = beat
	_flags = flags.duplicate()
	_skipped = false
	_pending_choice_beat_id = ""
	if _beats_order.is_empty():
		finished.emit(_sequence_id)
		return
	_run_beat(_beats_order[0].get("id", ""))


func skip() -> void:
	_skipped = true
	_pending_choice_beat_id = ""
	finished.emit(_sequence_id)


func resolve_choice(option_id: String) -> void:
	if _pending_choice_beat_id.is_empty():
		return
	var beat: Dictionary = _beats_by_id.get(_pending_choice_beat_id, {})
	var next_id: String = _choice_resolver.resolve(beat, option_id)
	if next_id.is_empty():
		push_error("CutsceneDirector: no choice option '%s' on beat '%s'" % [option_id, _pending_choice_beat_id])
		return
	_pending_choice_beat_id = ""
	_continue_to(next_id)


func _run_beat(beat_id: String) -> void:
	if beat_id.is_empty() or not _beats_by_id.has(beat_id):
		if not _skipped:
			finished.emit(_sequence_id)
		return

	var beat: Dictionary = _beats_by_id[beat_id]
	beat_started.emit(beat)

	match beat.get("type", ""):
		"dialogue":
			await _dialogue_runner.run(beat, get_tree())
			if _skipped:
				return
			_advance_after(beat_id)
		"wait":
			await get_tree().create_timer(beat.get("duration", 0.0)).timeout
			if _skipped:
				return
			_advance_after(beat_id)
		"animation_cue":
			if beat.has("duration"):
				await get_tree().create_timer(beat.get("duration")).timeout
				if _skipped:
					return
			_advance_after(beat_id)
		"choice":
			_pending_choice_beat_id = beat_id
			choice_requested.emit(beat)
		"branch":
			var condition_met: bool = _condition_evaluator.evaluate(beat.get("when", {}), _flags)
			var next_id: String = beat.get("then", "") if condition_met else beat.get("else", "")
			_continue_to(next_id)
		_:
			push_error("CutsceneDirector: unknown beat type '%s' on beat '%s'" % [beat.get("type", ""), beat_id])
			if not _skipped:
				finished.emit(_sequence_id)


func _advance_after(beat_id: String) -> void:
	_continue_to(_next_beat_id_after(beat_id))


func _continue_to(next_id: String) -> void:
	if next_id.is_empty():
		if not _skipped:
			finished.emit(_sequence_id)
		return
	_run_beat(next_id)


func _next_beat_id_after(beat_id: String) -> String:
	for i in _beats_order.size():
		if _beats_order[i].get("id", "") == beat_id:
			if i + 1 < _beats_order.size():
				return _beats_order[i + 1].get("id", "")
			return ""
	return ""
