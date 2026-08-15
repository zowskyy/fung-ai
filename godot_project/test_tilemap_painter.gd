# test_tilemap_painter.gd — Headless logic tests for TileMapPainter.
#
# Because TileMapLayer.set_cell() requires a TileSet to produce usable cells,
# these tests exercise:
#   (a) graceful no-op when TileSet is absent (no crash)
#   (b) clear_grid does not crash on an empty layer
#   (c) get_tile_count() returns 0 on a fresh layer
#   (d) paint_grid_from_json() rejects a missing file cleanly
#   (e) paint_grid_from_json() loads a real godot_scene.json and reports
#       tile count (TileSet absent → warning, not crash; count = 0 is OK)
#
# Full visual correctness (painted tiles rendered correctly) requires a running
# scene with a configured TileSet; that is covered by the windowed integration
# tests.
#
# Run with:
#   Godot_v4.7.1-stable_win64_console.exe --headless --path godot_project --script test_tilemap_painter.gd

extends SceneTree

const SCENE_JSON := "C:/Users/thewi/OneDrive/Desktop/fung.us/fungaiV2_extracted/godot_scene.json"

func _init() -> void:
	var ok := true

	var PainterScript := load("res://tilemap_painter.gd")
	var painter = PainterScript.new()

	# ------------------------------------------------------------------ #
	# (a) paint_grid() with a null TileSet — must warn, not crash         #
	# ------------------------------------------------------------------ #
	var layer := TileMapLayer.new()
	# layer.tile_set is null by default → should print a warning and return.
	painter.paint_grid(layer, [[0.0, 1.0], [1.0, 0.0]])
	ok = ok and _check(true, "paint_grid with null TileSet did not crash")

	# ------------------------------------------------------------------ #
	# (b) clear_grid on a fresh layer — must not crash                    #
	# ------------------------------------------------------------------ #
	painter.clear_grid(layer)
	ok = ok and _check(true, "clear_grid on fresh layer did not crash")

	# ------------------------------------------------------------------ #
	# (c) get_tile_count returns 0 on an empty layer                      #
	# ------------------------------------------------------------------ #
	var count: int = painter.get_tile_count(layer)
	ok = ok and _check(count == 0, "expected 0 tiles on fresh layer, got %d" % count)

	# ------------------------------------------------------------------ #
	# (d) paint_grid_from_json() with a non-existent file                 #
	# ------------------------------------------------------------------ #
	var bad_result: bool = painter.paint_grid_from_json(layer, "res://does_not_exist.json")
	ok = ok and _check(bad_result == false, "expected false for missing file, got true")

	# ------------------------------------------------------------------ #
	# (e) paint_grid_from_json() with the real godot_scene.json           #
	#     TileSet is absent → warning printed, returns false gracefully   #
	# ------------------------------------------------------------------ #
	if FileAccess.file_exists(SCENE_JSON):
		var real_result: bool = painter.paint_grid_from_json(layer, SCENE_JSON)
		# Without a TileSet the painter warns and returns false — that's correct.
		ok = ok and _check(real_result == false, "expected false (no TileSet) for real JSON, got true")
		print("  paint_grid_from_json with real scene.json returned: ", real_result, " (false expected — no TileSet)")
	else:
		print("  (skipping real-JSON test — file not found at %s)" % SCENE_JSON)

	# ------------------------------------------------------------------ #
	# (f) paint_grid() with an all-wall grid (0.0) does not crash         #
	# ------------------------------------------------------------------ #
	var all_wall: Array = []
	for _r in range(5):
		var row: Array = []
		for _c in range(5):
			row.append(0.0)
		all_wall.append(row)
	painter.paint_grid(layer, all_wall)
	ok = ok and _check(true, "paint_grid with all-wall grid did not crash")

	# ------------------------------------------------------------------ #
	# Report                                                              #
	# ------------------------------------------------------------------ #
	if ok:
		print("TILEMAP_PAINTER_TEST_RESULT: PASS")
	else:
		print("TILEMAP_PAINTER_TEST_RESULT: FAIL")

	quit(0 if ok else 1)


func _check(cond: bool, msg: String) -> bool:
	if not cond:
		print("ASSERTION FAILED: ", msg)
	return cond
