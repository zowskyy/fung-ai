extends SceneTree

# Headless smoke test for the fung_godot addon. Verifies the dock UI tree
# actually builds (catches @onready-without-a-scene mistakes), the backend
# client / export service helper methods behave correctly, and the RLE grid
# encoding produced by bridge/generation.py's encode_grid_rle() decodes back
# correctly in fung_export_service.gd (cross-language contract check).
#
# All setup and assertions run from _process(), not _initialize(): a node's
# _ready() only fires synchronously on add_child() once the SceneTree is
# actually running its frame loop, which _initialize() runs before (proven
# empirically - a first version of this test that built nodes in
# _initialize() saw every @onready-populated field come back null even
# though the same code works correctly in-editor).

var _passed: bool = true
var _started: bool = false


func _process(_delta: float) -> bool:
	if _started:
		return true
	_started = true

	_run_tests()

	if _passed:
		print("test_dock_smoke: PASS")
		quit(0)
	else:
		print("test_dock_smoke: FAIL")
		quit(1)
	return true


func _run_tests() -> void:
	_test_dock_builds_tab_tree()
	_test_generate_tab_defaults()
	_test_candidates_tab_defaults()
	_test_export_tab_defaults()
	_test_library_tab_defaults()
	_test_backend_client_json_helpers()
	_test_export_service_rle_decode()
	_test_export_service_scene_path()
	_test_manifest_service_round_trip()


func _check(condition: bool, message: String) -> void:
	if not condition:
		push_error("FAIL: %s" % message)
		_passed = false


func _test_dock_builds_tab_tree() -> void:
	var dock_scene: PackedScene = load("res://addons/fung_godot/ui/fung_dock.tscn")
	var dock: FungDock = dock_scene.instantiate()
	root.add_child(dock)

	_check(dock.tab_container != null, "dock.tab_container should be built by _ready()")
	_check(dock.generate_tab != null, "dock.generate_tab should be instantiated")
	_check(dock.candidates_tab != null, "dock.candidates_tab should be instantiated")
	_check(dock.export_tab != null, "dock.export_tab should be instantiated")

	if dock.tab_container != null:
		_check(
			dock.tab_container.get_child_count() == 5,
			"dock should have 5 tabs (Generate, Candidates, Export, Environment, Library), got %d"
			% dock.tab_container.get_child_count()
		)

	if dock.generate_tab != null:
		_check(
			dock.generate_tab.recipe_selector != null,
			"generate_tab.recipe_selector should be built by its own _ready(), nested under dock"
		)

	_check(dock.library_tab != null, "dock.library_tab should be instantiated")
	if dock.library_tab != null:
		_check(
			dock.library_tab.manifest_list != null,
			"library_tab.manifest_list should be built by its own _ready(), nested under dock"
		)

	dock.queue_free()


func _test_generate_tab_defaults() -> void:
	var tab: FungGenerateTab = FungGenerateTab.new()
	root.add_child(tab)

	_check(tab.recipe_selector != null, "recipe_selector should exist")
	_check(
		tab.recipe_selector.item_count == 3,
		"recipe_selector should have 3 recipes, got %d" % tab.recipe_selector.item_count
	)
	_check(tab.width_spin.value == 96.0, "width_spin should default to 96")
	_check(tab.height_spin.value == 96.0, "height_spin should default to 96")
	_check(tab.budget_selector.item_count == 3, "budget_selector should have 3 budget options")
	_check(tab.cancel_btn.disabled, "cancel_btn should start disabled")
	_check(tab.get_current_response_path() == "", "response path should start empty")

	tab.queue_free()


func _test_candidates_tab_defaults() -> void:
	var tab: FungCandidatesTab = FungCandidatesTab.new()
	root.add_child(tab)

	_check(tab.candidate_list != null, "candidate_list should exist")
	_check(tab.export_btn.disabled, "export_btn should start disabled with no candidates")

	tab.queue_free()


func _test_export_tab_defaults() -> void:
	var tab: FungExportTab = FungExportTab.new()
	root.add_child(tab)

	_check(tab.tileset_path_edit != null, "tileset_path_edit should exist")
	_check(tab.profile_selector.item_count == 3, "profile_selector should have 3 profiles")
	_check(tab.export_btn.disabled, "export_btn should start disabled with no candidate/tileset")

	tab.set_selected_candidate("candidate_001", "user://fake/result.json")
	_check(
		tab.export_name_edit.text == "candidate_001",
		"selecting a candidate should populate the export name field"
	)

	tab.queue_free()


func _test_library_tab_defaults() -> void:
	var tab: FungLibraryTab = FungLibraryTab.new()
	root.add_child(tab)

	_check(tab.manifest_list != null, "manifest_list should exist")
	_check(
		tab.regenerate_btn.disabled,
		"regenerate_btn should start disabled with no manifest selected"
	)

	tab.queue_free()


func _test_backend_client_json_helpers() -> void:
	var client: FungBackendClient = FungBackendClient.new()
	root.add_child(client)

	_check(client.is_idle(), "backend client should start idle")

	var missing: Dictionary = client._read_json_safe("user://does_not_exist_%d.json" % randi())
	_check(missing.is_empty(), "_read_json_safe should return {} for a missing file")

	var tmp_path: String = "user://fung_smoke_status.json"
	var file: FileAccess = FileAccess.open(tmp_path, FileAccess.WRITE)
	file.store_string('{"state": "running", "progress": 0.5}')
	file.close()

	var parsed: Dictionary = client._read_json_safe(tmp_path)
	_check(parsed.get("state", "") == "running", "_read_json_safe should parse written JSON")
	_check(parsed.get("progress", 0.0) == 0.5, "_read_json_safe should preserve numeric fields")

	DirAccess.remove_absolute(ProjectSettings.globalize_path(tmp_path))
	client.queue_free()


func _test_export_service_rle_decode() -> void:
	var service: FungExportService = FungExportService.new()
	root.add_child(service)

	# Matches bridge/generation.py's encode_grid_rle() for grid [[0,1],[1,0]]
	# flattened row-major: [0, 1, 1, 0] -> "rle-v1:1:0:2:1:1:0"
	var decoded: PackedByteArray = service._decode_grid("rle-v1:1:0:2:1:1:0", 2, 2)
	var expected: PackedByteArray = PackedByteArray([0, 1, 1, 0])
	_check(decoded == expected, "RLE decode mismatch: got %s expected %s" % [decoded, expected])

	var bad_size: PackedByteArray = service._decode_grid("rle-v1:1:0", 2, 2)
	_check(bad_size.is_empty(), "_decode_grid should reject a size mismatch")

	var no_prefix: PackedByteArray = service._decode_grid("not-rle-data", 2, 2)
	_check(no_prefix.is_empty(), "_decode_grid should reject data without the rle-v1 prefix")

	service.queue_free()


func _test_export_service_scene_path() -> void:
	var service: FungExportService = FungExportService.new()
	root.add_child(service)

	var scene_path: String = service._get_export_scene_path("candidate_001")
	_check(
		not scene_path.contains("//levels"),
		"export scene path should not contain a double slash: %s" % scene_path
	)
	_check(
		scene_path.ends_with("levels/candidate_001.tscn"),
		"export scene path should end with levels/candidate_001.tscn: %s" % scene_path
	)

	service.queue_free()


func _test_manifest_service_round_trip() -> void:
	var service: FungManifest = FungManifest.new()
	root.add_child(service)

	# Point the service at a scratch directory under user:// so this test
	# never writes into the checked-out res:// tree - matches
	# _test_backend_client_json_helpers' pattern of writing/reading a real
	# file under user:// and cleaning it up after.
	var tmp_root: String = "user://fung_smoke_manifests/"
	service._manifest_root = tmp_root
	DirAccess.make_dir_recursive_absolute(tmp_root)

	var candidate_data: Dictionary = {
		"seed": 12345,
		"recipe_id": "compact_roguelike_rooms",
		"fung_version": "0.1.0",
		"map_size_tiles": [96, 96],
		"metrics": {"walkable_ratio": 0.43, "path_length": 67, "loop_count": 3},
		"preview_path": "previews/candidate_001.png",
	}

	var wrote: bool = service.write_manifest(
		"smoke_test_scene",
		candidate_data,
		"top_down_default",
		"res://generated/fung/levels/smoke_test_scene.tscn",
	)
	_check(wrote, "write_manifest should return true on success")

	var read_back: Dictionary = service.read_manifest("smoke_test_scene")
	_check(not read_back.is_empty(), "read_manifest should return a non-empty dict after writing")
	_check(
		read_back.get("recipe_id", "") == "compact_roguelike_rooms",
		"read_manifest should round-trip recipe_id"
	)
	_check(int(read_back.get("seed", -1)) == 12345, "read_manifest should round-trip seed")
	_check(
		int(read_back.get("format_version", 0)) == 1,
		"read_manifest should round-trip format_version"
	)
	_check(
		String(read_back.get("created_utc", "")).ends_with("Z"),
		"created_utc should end with a Z (UTC marker)"
	)

	var listed: Array[Dictionary] = service.list_manifests()
	_check(
		listed.size() == 1,
		"list_manifests should find the manifest just written, got %d" % listed.size()
	)

	# Clean up: remove the manifest file and the scratch directory.
	var manifest_path: String = tmp_root.path_join("smoke_test_scene.fung.json")
	DirAccess.remove_absolute(ProjectSettings.globalize_path(manifest_path))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(tmp_root))

	service.queue_free()
