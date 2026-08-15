@tool
extends Control

class_name FungCandidatesTab

## Candidates tab: browse generated candidates with metrics and tags.

signal candidate_selected(candidate_id: String, candidate_data: Dictionary)
signal candidate_export_requested(candidate_id: String)

var _candidates: Array[Dictionary] = []
var _selected_candidate_idx: int = -1
var _result_path: String = ""

@onready var candidate_list: ItemList = $CandidateList
@onready var preview_rect: TextureRect = $PreviewRect
@onready var metrics_label: Label = $MetricsLabel
@onready var tags_label: Label = $TagsLabel
@onready var export_btn: Button = $ExportBtn


func _ready() -> void:
	if not Engine.is_editor_hint():
		return

	_setup_signals()
	_update_empty_state()


func load_results(result_path: String) -> bool:
	"""Load candidates from result.json file."""
	if not ResourceLoader.exists(result_path):
		_clear_candidates()
		metrics_label.text = "No results found"
		return false

	_result_path = result_path
	var result_data: Dictionary = _read_json_safe(result_path)

	if result_data.is_empty():
		_clear_candidates()
		metrics_label.text = "Failed to load results"
		return false

	_candidates.clear()
	candidate_list.clear()
	_selected_candidate_idx = -1

	for candidate in result_data.get("candidates", []):
		_candidates.append(candidate)
		var candidate_id: String = candidate.get("candidate_id", "")
		var tags: Array = candidate.get("tags", [])
		var tag_str: String = ", ".join(tags) if tags.size() > 0 else "No tags"
		candidate_list.add_item("%s [%s]" % [candidate_id, tag_str])

	if _candidates.is_empty():
		_update_empty_state()
		return false

	# Select first candidate by default
	candidate_list.select(0)
	_on_candidate_selected(0)
	return true


func _setup_signals() -> void:
	"""Connect control signals."""
	candidate_list.item_selected.connect(_on_candidate_selected)
	export_btn.pressed.connect(_on_export_pressed)


func _on_candidate_selected(index: int) -> void:
	"""Handle candidate selection."""
	if index < 0 or index >= _candidates.size():
		_update_empty_state()
		return

	_selected_candidate_idx = index
	var candidate: Dictionary = _candidates[index]

	# Update display
	_update_metrics_display(candidate)
	_load_preview(candidate)

	candidate_selected.emit(candidate.get("candidate_id", ""), candidate)
	export_btn.disabled = false


func _on_export_pressed() -> void:
	"""Request export of selected candidate."""
	if _selected_candidate_idx >= 0 and _selected_candidate_idx < _candidates.size():
		var candidate: Dictionary = _candidates[_selected_candidate_idx]
		candidate_export_requested.emit(candidate.get("candidate_id", ""))


func _update_metrics_display(candidate: Dictionary) -> void:
	"""Update metrics and tags display."""
	var metrics: Dictionary = candidate.get("metrics", {})
	var tags: Array = candidate.get("tags", [])

	var metrics_text: String = "Metrics:\n"
	metrics_text += "  Walkable Ratio: %.1f%%\n" % (metrics.get("walkable_ratio", 0.0) * 100.0)
	metrics_text += "  Path Length: %.0f\n" % metrics.get("path_length", 0.0)
	metrics_text += "  Loop Count: %.0f\n" % metrics.get("loop_count", 0.0)
	metrics_text += "  Branch Count: %.0f\n" % metrics.get("branch_count", 0.0)
	metrics_text += "  Open Space: %.2f" % metrics.get("open_space_score", 0.0)

	metrics_label.text = metrics_text

	var tag_str: String = "Tags: " + ", ".join(tags) if tags.size() > 0 else "Tags: None"
	tags_label.text = tag_str


func _load_preview(candidate: Dictionary) -> void:
	"""Load preview image for candidate."""
	var preview_path: String = candidate.get("preview_path", "")
	if preview_path.is_empty():
		preview_rect.texture = null
		return

	# Construct full path from job_dir (we'd need to pass this from parent)
	# For now, just show a placeholder
	preview_rect.texture = null


func _update_empty_state() -> void:
	"""Show empty state UI."""
	candidate_list.clear()
	preview_rect.texture = null
	metrics_label.text = "No candidates loaded"
	tags_label.text = ""
	export_btn.disabled = true


func _clear_candidates() -> void:
	"""Clear all candidates."""
	_candidates.clear()
	_selected_candidate_idx = -1
	_update_empty_state()


func _read_json_safe(path: String) -> Dictionary:
	"""Safely read and parse JSON file."""
	if not ResourceLoader.exists(path):
		return {}

	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}

	var text: String = file.get_as_text()
	var json: JSON = JSON.new()
	var error: Error = json.parse(text)

	if error != OK:
		return {}

	var data: Variant = json.data
	if data is Dictionary:
		return data

	return {}
