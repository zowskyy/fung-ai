@tool
extends Control

class_name FungGenerateTab

## Generate tab: recipe selection, seed management, generation control.

signal generate_requested(request_id: String, request_path: String, response_path: String, job_dir: String)
signal generation_progress(progress: float, stage: String, message: String)
signal generation_completed(success: bool, error_message: String)

var _backend_client: FungBackendClient = null
var _candidates_tab: FungCandidatesTab = null
var _job_counter: int = 0
var _current_request_id: String = ""
var _current_response_path: String = ""

@onready var recipe_selector: OptionButton = $RecipeSelector
@onready var width_spin: SpinBox = $MapSizeContainer/WidthSpin
@onready var height_spin: SpinBox = $MapSizeContainer/HeightSpin
@onready var seed_spin: SpinBox = $SeedContainer/SeedSpin
@onready var randomize_btn: Button = $SeedContainer/RandomizeBtn
@onready var budget_selector: OptionButton = $BudgetSelector
@onready var generate_btn: Button = $GenerateBtn
@onready var cancel_btn: Button = $CancelBtn
@onready var progress_bar: ProgressBar = $ProgressBar
@onready var progress_label: Label = $ProgressLabel
@onready var status_label: Label = $StatusLabel


func _ready() -> void:
	if not Engine.is_editor_hint():
		return

	_setup_ui()
	_setup_signals()


func set_backend_client(backend_client: FungBackendClient) -> void:
	"""Set reference to backend client service."""
	_backend_client = backend_client
	if _backend_client:
		_backend_client.generation_started.connect(_on_generation_started)
		_backend_client.generation_progress.connect(_on_generation_progress)
		_backend_client.generation_completed.connect(_on_generation_completed)
		_backend_client.generation_cancelled.connect(_on_generation_cancelled)


func set_candidates_tab(candidates_tab: FungCandidatesTab) -> void:
	"""Set reference to candidates tab for auto-loading results."""
	_candidates_tab = candidates_tab


func _setup_ui() -> void:
	"""Initialize UI controls."""
	# Recipe selector
	recipe_selector.add_item("compact_roguelike_rooms", 0)
	recipe_selector.add_item("open_exploration", 1)
	recipe_selector.add_item("dense_maze", 2)
	recipe_selector.select(0)

	# Map size
	width_spin.value = 96.0
	height_spin.value = 96.0

	# Seed
	seed_spin.value = 0.0
	seed_spin.max_value = 2147483647.0  # Max 32-bit int

	# Budget
	budget_selector.add_item("Fast (3 candidates)", 0)
	budget_selector.add_item("Balanced (6 candidates)", 1)
	budget_selector.add_item("Thorough (12 candidates)", 2)
	budget_selector.select(1)

	# Progress
	progress_bar.value = 0.0
	progress_label.text = "Ready"
	status_label.text = ""


func _setup_signals() -> void:
	"""Connect UI control signals."""
	randomize_btn.pressed.connect(_on_randomize_seed)
	generate_btn.pressed.connect(_on_generate_pressed)
	cancel_btn.pressed.connect(_on_cancel_pressed)
	cancel_btn.disabled = true


func _on_randomize_seed() -> void:
	"""Generate random seed."""
	seed_spin.value = randi() % int(seed_spin.max_value)


func _on_generate_pressed() -> void:
	"""Start generation with current settings."""
	if not _backend_client or not _backend_client.is_idle():
		status_label.text = "Backend not ready"
		return

	_current_request_id = "fung_%d_%d" % [Time.get_ticks_msec(), _job_counter]
	_job_counter += 1

	# Build request
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

	# Ensure job directory exists
	DirAccess.make_absolute_path(job_dir, "user://")

	# Store response path for later loading
	_current_response_path = response_path

	# Build request JSON
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

	# Write request atomically
	var file: FileAccess = FileAccess.open(request_path, FileAccess.WRITE)
	if file == null:
		status_label.text = "Failed to write request"
		return

	var json_str: String = JSON.stringify(request, "\t")
	file.store_string(json_str)
	file.flush()

	# Launch generation
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
	"""Cancel current generation."""
	if _backend_client:
		_backend_client.cancel_generation()


func _on_generation_started(request_id: String) -> void:
	"""Backend signal: generation started."""
	progress_label.text = "Running..."
	status_label.text = "Initializing generation..."


func _on_generation_progress(
	request_id: String,
	progress: float,
	stage: String,
	message: String,
) -> void:
	"""Backend signal: generation progress update."""
	progress_bar.value = int(progress * 100.0)
	progress_label.text = "%s (%.0f%%)" % [stage, progress * 100.0]
	status_label.text = message


func _on_generation_completed(request_id: String, success: bool, error_message: String) -> void:
	"""Backend signal: generation completed."""
	progress_label.text = "Completed" if success else "Failed"

	if success:
		status_label.text = "Generation complete - loading results..."
		progress_bar.value = 100

		# Auto-load results into candidates tab
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


func _on_generation_cancelled(request_id: String) -> void:
	"""Backend signal: generation cancelled."""
	progress_label.text = "Cancelled"
	status_label.text = "Generation was cancelled"
	progress_bar.value = 0
	generate_btn.disabled = false
	cancel_btn.disabled = true


func _get_job_dir(request_id: String) -> String:
	"""Get job directory path."""
	return "user://.fung/jobs/%s" % request_id
