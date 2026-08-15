extends SceneTree

const REPLAY_PATH := "res://examples/cave_boss/replay.json"


func _initialize() -> void:
	if not FileAccess.file_exists(REPLAY_PATH):
		printerr("replay_check: replay.json not found at %s" % REPLAY_PATH)
		quit(1)
		return

	var file := FileAccess.open(REPLAY_PATH, FileAccess.READ)
	if file == null:
		printerr("replay_check: failed to open replay.json: %s" % error_string(FileAccess.get_open_error()))
		quit(1)
		return

	var text := file.get_as_text()
	file.close()

	var parsed = JSON.parse_string(text)
	if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
		printerr("replay_check: replay.json is not valid JSON")
		quit(1)
		return

	var replay: Dictionary = parsed
	if not replay.has("seed"):
		printerr("replay_check: replay.json missing 'seed'")
		quit(1)
		return
	if not replay.has("final_hash") or typeof(replay.final_hash) != TYPE_STRING or replay.final_hash.is_empty():
		printerr("replay_check: replay.json missing/invalid 'final_hash'")
		quit(1)
		return

	# Full deterministic re-simulation (re-running main.tscn with the same
	# seed and diffing final_hash against this file) is not implemented yet -
	# this checks structural validity only, per the project brief's explicit
	# "stub full re-simulation for now".
	print("replay_check: PASS - seed=%s final_hash=%s" % [replay.seed, replay.final_hash])
	quit(0)
