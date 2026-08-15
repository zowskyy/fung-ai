extends SceneTree

const MAIN_SCENE_PATH := "res://examples/cave_boss/main.tscn"
const DEFAULT_TIMEOUT_S := 30.0

var _timeout_s: float = DEFAULT_TIMEOUT_S
var _start_msec: int = 0
var _done := false


func _initialize() -> void:
	_start_msec = Time.get_ticks_msec()
	_timeout_s = _parse_timeout_arg()
	# --seed= is consumed directly by main.gd via OS.get_cmdline_args(); it is
	# only re-parsed here so the runner can log what generation mode is used.
	print("run_example: seed=%s timeout=%.1fs" % [_parse_seed_arg(), _timeout_s])

	print("run_example: loading scene from %s" % MAIN_SCENE_PATH)
	var packed_scene: PackedScene = load(MAIN_SCENE_PATH)
	if packed_scene == null:
		printerr("run_example: failed to load scene at %s" % MAIN_SCENE_PATH)
		quit(1)
		return

	print("run_example: scene loaded, instantiating...")
	var main_instance := packed_scene.instantiate()
	if not main_instance.has_signal("scene_finished"):
		printerr("run_example: main scene root has no 'scene_finished' signal")
		quit(1)
		return

	print("run_example: connecting signal and adding to scene tree...")
	main_instance.scene_finished.connect(_on_scene_finished)
	root.add_child(main_instance)
	print("run_example: scene added to tree, waiting for completion...")


func _parse_timeout_arg() -> float:
	for arg in OS.get_cmdline_args():
		if arg.begins_with("--timeout="):
			return float(arg.substr("--timeout=".length()))
	return DEFAULT_TIMEOUT_S


func _parse_seed_arg() -> String:
	for arg in OS.get_cmdline_args():
		if arg.begins_with("--seed="):
			return arg.substr("--seed=".length())
	return "(pre-generated cave)"


func _on_scene_finished(success: bool, message: String) -> void:
	if _done:
		return
	_done = true
	if success:
		print("run_example: SUCCESS - %s" % message)
		quit(0)
	else:
		printerr("run_example: FAILURE - %s" % message)
		quit(1)


func _process(_delta: float) -> bool:
	if _done:
		return true
	var elapsed_s := (Time.get_ticks_msec() - _start_msec) / 1000.0
	if elapsed_s > _timeout_s:
		_done = true
		printerr("run_example: TIMEOUT after %.1fs" % elapsed_s)
		quit(2)
		return true
	return false
