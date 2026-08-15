# test_ca_bridge.gd — Headless smoke-test for CaBridge.
#
# Run with:
#   Godot_v4.7.1-stable_win64_console.exe --headless --path godot_project --script test_ca_bridge.gd
#
# Exit 0 = PASS, Exit 1 = FAIL.

extends SceneTree

func _init() -> void:
	var ok := true

	# ------------------------------------------------------------------ #
	# 1. Instantiate bridge and check path helpers                        #
	# ------------------------------------------------------------------ #
	var BridgeScript := load("res://ca_bridge.gd")
	var bridge = BridgeScript.new()

	var py_exe: String = bridge.get_python_exe()
	ok = ok and _check(py_exe != "", "get_python_exe() returned empty string")
	print("  python exe: ", py_exe)

	var cli_path: String = bridge.get_ca_script_path()
	ok = ok and _check(cli_path != "", "get_ca_script_path() found nothing — check that fung_ai_v2/cli.py or fungaiV2_extracted/fung_ai_v2.py exists")
	print("  cli path:   ", cli_path)

	# ------------------------------------------------------------------ #
	# 2. Actually call Python and get a grid back                         #
	# ------------------------------------------------------------------ #
	print("  calling generate(rule=B3/S23, width=20, height=20, ticks=5, seed=42) ...")
	var result: Dictionary = bridge.generate("B3/S23", 20, 20, 5, 42)

	if result.is_empty():
		ok = _check(false, "generate() returned empty dict — Python call failed (check push_error output above)")
	else:
		ok = ok and _check(result.has("grid"),     "result missing 'grid' key")
		ok = ok and _check(result.has("rule"),     "result missing 'rule' key")
		ok = ok and _check(result.has("playable"), "result missing 'playable' key")
		ok = ok and _check(result.has("width"),    "result missing 'width' key")
		ok = ok and _check(result.has("height"),   "result missing 'height' key")

		if result.has("grid"):
			var grid: Array = result["grid"]
			ok = ok and _check(grid.size() == 20, "expected 20 rows, got %d" % grid.size())
			if grid.size() > 0:
				ok = ok and _check((grid[0] as Array).size() == 20, "expected 20 cols, got %d" % (grid[0] as Array).size())

		print("  rule=%s  playable=%s  coverage=%s" % [
			str(result.get("rule", "?")),
			str(result.get("playable", "?")),
			str(result.get("coverage", "?")),
		])

	# ------------------------------------------------------------------ #
	# 3. Report                                                           #
	# ------------------------------------------------------------------ #
	if ok:
		print("CA_BRIDGE_TEST_RESULT: PASS")
	else:
		print("CA_BRIDGE_TEST_RESULT: FAIL")

	quit(0 if ok else 1)


func _check(cond: bool, msg: String) -> bool:
	if not cond:
		print("ASSERTION FAILED: ", msg)
	return cond
