@tool
extends Control

class_name FungCandidatesTab

# Candidates tab: browse generated candidates with metrics and tags.
# Builds its own child controls in code (no backing .tscn).

signal candidate_selected(candidate_id: String, candidate_data: Dictionary)
signal candidate_export_requested(candidate_id: String)

var _candidates: Array = []
var _selected_candidate_idx: int = -1
var _result_path: String = ""

var candidate_list: ItemList
var preview_rect: TextureRect
var metrics_label: Label
var tags_label: Label
var export_btn: Button


func _ready() -> void:
	_build_ui()
	_setup_signals()
	_update_empty_state()


func load_results(result_path: String) -> bool:
	# Load candidates from result.json file.
	if not FileAccess.file_exists(result_path):
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

	candidate_list.select(0)
	_on_candidate_selected(0)
	return true


func _build_ui() -> void:
	var layout: HBoxContainer = HBoxContainer.new()
	layout.name = "Layout"
	layout.anchor_right = 1.0
	layout.anchor_bottom = 1.0
	add_child(layout)

	candidate_list = ItemList.new()
	candidate_list.name = "CandidateList"
	candidate_list.custom_minimum_size = Vector2(200, 0)
	layout.add_child(candidate_list)

	var detail_column: VBoxContainer = VBoxContainer.new()
	detail_column.name = "DetailColumn"
	layout.add_child(detail_column)

	preview_rect = TextureRect.new()
	preview_rect.name = "PreviewRect"
	preview_rect.custom_minimum_size = Vector2(128, 128)
	detail_column.add_child(preview_rect)

	metrics_label = Label.new()
	metrics_label.name = "MetricsLabel"
	metrics_label.text = "No candidates loaded"
	detail_column.add_child(metrics_label)

	tags_label = Label.new()
	tags_label.name = "TagsLabel"
	detail_column.add_child(tags_label)

	export_btn = Button.new()
	export_btn.name = "ExportBtn"
	export_btn.text = "Export"
	export_btn.disabled = true
	detail_column.add_child(export_btn)


func _setup_signals() -> void:
	candidate_list.item_selected.connect(_on_candidate_selected)
	export_btn.pressed.connect(_on_export_pressed)


func _on_candidate_selected(index: int) -> void:
	if index < 0 or index >= _candidates.size():
		_update_empty_state()
		return

	_selected_candidate_idx = index
	var candidate: Dictionary = _candidates[index]

	_update_metrics_display(candidate)
	_load_preview(candidate)

	candidate_selected.emit(candidate.get("candidate_id", ""), candidate)
	export_btn.disabled = false


func _on_export_pressed() -> void:
	if _selected_candidate_idx >= 0 and _selected_candidate_idx < _candidates.size():
		var candidate: Dictionary = _candidates[_selected_candidate_idx]
		candidate_export_requested.emit(candidate.get("candidate_id", ""))


func _update_metrics_display(candidate: Dictionary) -> void:
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
	# Load preview image for candidate, resolved relative to the job dir
	# (the parent of result.json).
	var preview_rel_path: String = candidate.get("preview_path", "")
	if preview_rel_path.is_empty() or _result_path.is_empty():
		preview_rect.texture = null
		return

	var job_dir: String = _result_path.get_base_dir()
	var preview_abs_path: String = job_dir.path_join(preview_rel_path)

	if not FileAccess.file_exists(preview_abs_path):
		preview_rect.texture = null
		return

	var image: Image = Image.new()
	var error: Error = image.load(preview_abs_path)
	if error != OK:
		preview_rect.texture = null
		return

	preview_rect.texture = ImageTexture.create_from_image(image)


func _update_empty_state() -> void:
	candidate_list.clear()
	preview_rect.texture = null
	metrics_label.text = "No candidates loaded"
	tags_label.text = ""
	export_btn.disabled = true


func _clear_candidates() -> void:
	_candidates.clear()
	_selected_candidate_idx = -1
	_update_empty_state()


func _read_json_safe(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
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
