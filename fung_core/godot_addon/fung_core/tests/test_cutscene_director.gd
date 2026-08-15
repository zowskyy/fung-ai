extends SceneTree

var _director: CutsceneDirector = null
var _actual_order: Array = []
var _expected_order: Array = ["d1", "c1", "b1", "end_a"]
var _passed: bool = true
var _done: bool = false
var _start_msec: int = 0

const TIMEOUT_MSEC: int = 8000


func _initialize() -> void:
	_start_msec = Time.get_ticks_msec()

	var sequence: Dictionary = {
		"version": 1,
		"sequence_id": "test_seq",
		"beats": [
			{
				"id": "d1",
				"type": "dialogue",
				"speaker": "npc",
				"text": "hello",
				"duration": 0.05
			},
			{
				"id": "c1",
				"type": "choice",
				"options": [
					{"id": "a", "label": "Pick A", "next": "b1"},
					{"id": "b", "label": "Pick B", "next": "b1"}
				]
			},
			{
				"id": "b1",
				"type": "branch",
				"when": {"flag": "picked_a", "equals": true},
				"then": "end_a",
				"else": "end_b"
			},
			{
				"id": "end_b",
				"type": "dialogue",
				"speaker": "npc",
				"text": "wrong branch",
				"duration": 0.05
			},
			{
				"id": "end_a",
				"type": "dialogue",
				"speaker": "npc",
				"text": "right branch",
				"duration": 0.05
			}
		]
	}

	_director = CutsceneDirector.new()
	root.add_child(_director)
	_director.beat_started.connect(_on_beat_started)
	_director.choice_requested.connect(_on_choice_requested)
	_director.finished.connect(_on_finished)

	_director.play(sequence, {"picked_a": true})


func _on_beat_started(beat: Dictionary) -> void:
	_actual_order.append(beat.get("id", ""))


func _on_choice_requested(beat: Dictionary) -> void:
	if beat.get("id", "") != "c1":
		push_error("choice_requested fired for unexpected beat '%s'" % beat.get("id", ""))
		_passed = false
	_director.resolve_choice("a")


func _on_finished(sequence_id: String) -> void:
	if sequence_id != "test_seq":
		push_error("finished emitted with unexpected sequence_id '%s'" % sequence_id)
		_passed = false
	if _actual_order != _expected_order:
		push_error("beat_started order mismatch: got %s expected %s" % [_actual_order, _expected_order])
		_passed = false
	_finish()


func _process(_delta: float) -> bool:
	if _done:
		return true
	if Time.get_ticks_msec() - _start_msec > TIMEOUT_MSEC:
		push_error("test_cutscene_director timed out waiting for 'finished'")
		_passed = false
		_finish()
		return true
	return false


func _finish() -> void:
	if _done:
		return
	_done = true
	if _passed:
		print("test_cutscene_director: PASS")
		quit(0)
	else:
		print("test_cutscene_director: FAIL")
		quit(1)
