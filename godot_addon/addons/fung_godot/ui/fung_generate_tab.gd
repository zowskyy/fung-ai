@tool
extends Control

class_name FungGenerateTab

# Generate tab: recipe selection, seed management, generation control.
# Builds its own child controls in code (no backing .tscn) so it can be
# instantiated with plain `.new()` from fung_dock.gd or a headless test.

signal generate_requested(request_id: String, request_path: String, response_path: String, job_dir: String)
signal generation_progress(progress: float, stage: String, message: String)
signal generation_completed(success: bool, error_message: String)

var _backend_client: FungBackendClient = null
var _candidates_tab: FungCandidatesTab = null
var _job_counter: int = 0
var _current_request_id: String = ""
var _current_response_path: String = ""

var recipe_selector: OptionButton
var width_spin: SpinBox
var height_spin: SpinBox
var seed_spin: SpinBox
var randomize_btn: Button
var budget_selector: OptionButton
var generate_btn: Button
var cancel_btn: Button
var progress_bar: ProgressBar
var progress_label: Label
var status_label: Label


func _ready() -> void:
	_build_ui()
	_setup_signals()


func set_backend_client(backend_client: FungBackendClient) -> void:
	# Set reference to backend client service.
	_backend_client = backend_client
	if _backend_client:
		_backend_client.generation_started.connect(_on_generation_started)
		_backend_client.generation_progress.connect(_on_generation_progress)
		_backend_client.generation_completed.connect(_on_generation_completed)
		_backend_client.generation_cancelled.connect(_on_generation_cancelled)


func set_candidates_tab(candidates_tab: FungCandidatesTab) -> void:
	# Set reference to candidates tab for auto-loading results.
	_candidates_tab = candidates_tab


func get_current_response_path() -> String:
	return _current_response_path


func prefill(recipe_id: String, seed: int, map_size_tiles: Array) -> void:
	# Pre-fill recipe/seed/map size from a manifest (Library tab's
	# "Regenerate from manifest"). Does not start generation by itself.
	for i in range(recipe_selector.item_count):
		if recipe_selector.get_item_text(i) == recipe_id:
			recipe_selector.select(i)
			break

	seed_spin.value = float(seed)

	if map_size_tiles.size() >= 2:
		width_spin.value = float(map_size_tiles[0])
		height_spin.value = float(map_size_tiles[1])

	status_label.text = "Prefilled from manifest: %s (seed %d)" % [recipe_id, seed]


func _build_ui() -> void:
	# Construct the control tree and set initial values.
	var layout: VBoxContainer = VBoxContainer.new()
	layout.name = "Layout"
	layout.anchor_right = 1.0
	layout.anchor_bottom = 1.0
	add_child(layout)

	recipe_selector = OptionButton.new()
	recipe_selector.name = "RecipeSelector"
	recipe_selector.add_item("compact_roguelike_rooms", 0)
	recipe_selector.add_item("open_exploration", 1)
	recipe_selector.add_item("dense_maze", 2)
	recipe_selector.select(0)
	layout.add_child(recipe_selector)

	var map_size_container: HBoxContainer = HBoxContainer.new()
	map_size_container.name = "MapSizeContainer"
	layout.add_child(map_size_container)

	width_spin = SpinBox.new()
	width_spin.name = "WidthSpin"
	width_spin.min_value = 8
	width_spin.max_value = 512
	width_spin.value = 96.0
	map_size_container.add_child(width_spin)

	height_spin = SpinBox.new()
	height_spin.name = "HeightSpin"
	height_spin.min_value = 8
	height_spin.max_value = 512
	height_spin.value = 96.0
	map_size_container.add_child(height_spin)

	var seed_container: HBoxContainer = HBoxContainer.new()
	seed_container.name = "SeedContainer"
	layout.add_child(seed_container)

	seed_spin = SpinBox.new()
	seed_spin.name = "SeedSpin"
	seed_spin.max_value = 2147483647.0  # Max 32-bit int
	seed_spin.value = 0.0
	seed_container.add_child(seed_spin)

	randomize_btn = Button.new()
	randomize_btn.name = "RandomizeBtn"
	randomize_btn.text = "Randomize"
	seed_container.add_child(randomize_btn)

	budget_selector = OptionButton.new()
	budget_selector.name = "BudgetSelector"
	budget_selector.add_item("Fast (3 candidates)", 0)
	budget_selector.add_item("Balanced (6 candidates)", 1)
	budget_selector.add_item("Thorough (12 candidates)", 2)
	budget_selector.select(1)
	layout.add_child(budget_selector)

	generate_btn = Button.new()
	generate_btn.name = "GenerateBtn"
	generate_btn.text = "Generate"
	layout.add_child(generate_btn)

	cancel_btn = Button.new()
	cancel_btn.name = "CancelBtn"
	cancel_btn.text = "Cancel"
	cancel_btn.disabled = true
	layout.add_child(cancel_btn)

	progress_bar = ProgressBar.new()
	progress_bar.name = "ProgressBar"
	progress_bar.value = 0.0
	layout.add_child(progress_bar)

	progress_label = Label.new()
	progress_label.name = "ProgressLabel"
	progress_label.text = "Ready"
	layout.add_child(progress_label)

	status_label = Label.new()
	status_label.name = "StatusLabel"
	status_label.text = ""
	layout.add_child(status_label)


func _setup_signals() -> void:
	# Connect UI control signals.
	randomize_btn.pressed.connect(_on_randomize_seed)
	generate_btn.pressed.connect(_on_generate_pressed)
	cancel_btn.pressed.connect(_on_cancel_pressed)


func _on_randomize_seed() -> void:
	# Generate random seed.
	seed_spin.value = randi() % int(seed_spin.max_value)


func _on_generate_pressed() -> void:
	# Start generation with current settings.
	if not _backend_client or not _backend_client.is_idle():
		status_label.text = "Backend not ready"
		return

	_current_request_id = "fung_%d_%d" % [Time.get_ticks_msec(), _job_counter]
	_job_counter += 1

	var recipe_id: String = recipe_selector.get_item_text(recipe_selector.get_selected_id())
	var seed: int = int(seed_spin.value)
	var width: int = int(width_spin.value)
	var height: int = int(height_spin.value)
	var budget_idx: int = budget_selector.get_selected_id()
	var budget: String = ["fast", "balanced", "thorough"][budget_idx]

	var job_dir: String = _get_job_dir(_current_request_id)
	var request_path: String = job_dir.path_join("request.json")
	var response_path: String = job_dir.path_join("result.json")
	var status_path: String = job_dir.path_join("status.json")
	var cancel_path: String = job_dir.path_join("cancel.request")

	DirAccess.make_dir_recursive_absolute(job_dir)

	_current_response_path = response_path

	var request: Dictionary = {
		"protocol_version": 1,
		"request_id": _current_request_id,
		"generator_version": "0.1.0",
		"recipe_id": recipe_id,
		"seed": seed,
		"map_size_tiles": [width, height],
		"tile_size_px": [16, 16],
		"generation_budget": budget,
		"environment_mode": "manual_preset",
		"environment_preset": "limestone_cave",
		"overrides": {},
		"candidate_count": 24,
		"job_dir": job_dir,
		"result_path": response_path,
		"status_path": status_path,
		"cancel_path": cancel_path,
	}

	var file: FileAccess = FileAccess.open(request_path, FileAccess.WRITE)
	if file == null:
		status_label.text = "Failed to write request"
		return

	var json_str: String = JSON.stringify(request, "\t")
	file.store_string(json_str)
	file.flush()

	progress_bar.value = 0.0
	generate_btn.disabled = true
	cancel_btn.disabled = false
	progress_label.text = "Launching..."

	var success: bool = _backend_client.start_generation(
		_current_request_id,
		request_path,
		response_path,
		job_dir,
	)

	if not success:
		status_label.text = "Failed to launch generation"
		progress_label.text = "Failed"
		generate_btn.disabled = false
		cancel_btn.disabled = true


func _on_cancel_pressed() -> void:
	# Cancel current generation.
	if _backend_client:
		_backend_client.cancel_generation()


func _on_generation_started(_request_id: String) -> void:
	progress_label.text = "Running..."
	status_label.text = "Initializing generation..."


func _on_generation_progress(
	_request_id: String,
	progress: float,
	stage: String,
	message: String,
) -> void:
	progress_bar.value = int(progress * 100.0)
	progress_label.text = "%s (%.0f%%)" % [stage, progress * 100.0]
	status_label.text = message


func _on_generation_completed(_request_id: String, success: bool, error_message: String) -> void:
	progress_label.text = "Completed" if success else "Failed"

	if success:
		status_label.text = "Generation complete - loading results..."
		progress_bar.value = 100

		if _candidates_tab:
			var loaded: bool = _candidates_tab.load_results(_current_response_path)
			if loaded:
				status_label.text = "Results loaded - browse in Candidates tab"
			else:
				status_label.text = "Generation complete, but failed to load results"
	else:
		status_label.text = "Error: %s" % error_message
		progress_bar.value = 0

	generate_btn.disabled = false
	cancel_btn.disabled = true
	generation_completed.emit(success, error_message)


func _on_generation_cancelled(_request_id: String) -> void:
	progress_label.text = "Cancelled"
	status_label.text = "Generation was cancelled"
	progress_bar.value = 0
	generate_btn.disabled = false
	cancel_btn.disabled = true


func _get_job_dir(request_id: String) -> String:
	return "user://.fung/jobs/%s" % request_id
