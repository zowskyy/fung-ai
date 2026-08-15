class_name ReplayRecorder
extends RefCounted

const VERSION := 1

var _seed: int = 0
var _frame: int = 0
var _input_sequence: Array = []


func start(seed: int) -> void:
	_seed = seed
	_frame = 0
	_input_sequence = []


func advance_frame() -> void:
	_frame += 1


func record_action(action: String, params: Dictionary = {}) -> void:
	var entry := {
		"frame": _frame,
		"action": action,
	}
	if not params.is_empty():
		entry["params"] = params
	_input_sequence.append(entry)


func finish(final_state: Dictionary) -> Dictionary:
	# Determinism relies on final_state already being canonically ordered by
	# the caller (see SnapshotSerializer) -- this only hashes what it is given.
	var final_hash := JSON.stringify(final_state).sha256_text()
	return {
		"version": VERSION,
		"seed": _seed,
		"input_sequence": _input_sequence,
		"final_hash": final_hash,
	}
