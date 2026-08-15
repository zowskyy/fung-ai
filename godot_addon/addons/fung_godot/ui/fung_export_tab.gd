@tool
extends Control

class_name FungExportTab

# Export tab: select TileSet, profile, and export settings.
# Builds its own child controls in code (no backing .tscn).

signal export_requested(
	result_path: String,
	candidate_id: String,
	tileset_path: String,
	export_profile: String,
)

var _export_service: FungExportService = null
var _selected_candidate_id: String = ""
var _result_path: String = ""

var tileset_path_edit: LineEdit
var profile_selector: OptionButton
var export_name_edit: LineEdit
var export_folder_edit: LineEdit
var layer_toggles_container: VBoxContainer
var export_btn: Button
var status_label: Label


func _ready() -> void:
	_build_ui()
	_setup_signals()
	_update_state()


func set_export_service(export_service: FungExportService) -> void:
	# Set reference to export service.
	_export_service = export_service
	if _export_service:
		_export_service.export_completed.connect(_on_export_completed)


func set_selected_candidate(candidate_id: String, result_path: String) -> void:
	# Set the candidate to export.
	_selected_candidate_id = candidate_id
	_result_path = result_path

	export_name_edit.text = candidate_id
	_update_state()


func _build_ui() -> void:
	var layout: VBoxContainer = VBoxContainer.new()
	layout.name = "Layout"
	layout.anchor_right = 1.0
	layout.anchor_bottom = 1.0
	add_child(layout)

	var tileset_container: HBoxContainer = HBoxContainer.new()
	tileset_container.name = "TileSetContainer"
	layout.add_child(tileset_container)

	tileset_path_edit = LineEdit.new()
	tileset_path_edit.name = "TileSetPath"
	tileset_path_edit.placeholder_text = "res://path/to/tileset.tres"
	tileset_container.add_child(tileset_path_edit)

	var browse_btn: Button = Button.new()
	browse_btn.name = "BrowseBtn"
	browse_btn.text = "Browse..."
	tileset_container.add_child(browse_btn)
	browse_btn.pressed.connect(_on_browse_tileset)

	profile_selector = OptionButton.new()
	profile_selector.name = "ProfileSelector"
	profile_selector.add_item("Top-Down (Default)", 0)
	profile_selector.add_item("Platformer (Default)", 1)
	profile_selector.add_item("Debug Visualization", 2)
	profile_selector.select(0)
	layout.add_child(profile_selector)

	var export_name_container: HBoxContainer = HBoxContainer.new()
	export_name_container.name = "ExportNameContainer"
	layout.add_child(export_name_container)

	export_name_edit = LineEdit.new()
	export_name_edit.name = "NameEdit"
	export_name_edit.text = "generated_level"
	export_name_edit.placeholder_text = "Scene name (no extension)"
	export_name_container.add_child(export_name_edit)

	var export_folder_container: HBoxContainer = HBoxContainer.new()
	export_folder_container.name = "ExportFolderContainer"
	layout.add_child(export_folder_container)

	export_folder_edit = LineEdit.new()
	export_folder_edit.name = "FolderEdit"
	export_folder_edit.text = "res://generated/fung/levels"
	export_folder_edit.placeholder_text = "res://... or user://..."
	export_folder_container.add_child(export_folder_edit)

	layer_toggles_container = VBoxContainer.new()
	layer_toggles_container.name = "LayerToggles"
	layout.add_child(layer_toggles_container)

	var layer_names: PackedStringArray = ["Terrain", "Collision", "Navigation", "Preview"]
	for layer_name in layer_names:
		var hbox: HBoxContainer = HBoxContainer.new()
		var check: CheckBox = CheckBox.new()
		check.button_pressed = true
		check.text = layer_name
		hbox.add_child(check)
		layer_toggles_container.add_child(hbox)

	export_btn = Button.new()
	export_btn.name = "ExportBtn"
	export_btn.text = "Export"
	export_btn.disabled = true
	layout.add_child(export_btn)

	status_label = Label.new()
	status_label.name = "StatusLabel"
	status_label.text = "Select candidate and TileSet"
	layout.add_child(status_label)


func _setup_signals() -> void:
	export_btn.pressed.connect(_on_export_pressed)
	tileset_path_edit.text_changed.connect(_on_tileset_changed)


func _on_browse_tileset() -> void:
	status_label.text = "TileSet browser not yet implemented"


func _on_tileset_changed(_new_text: String) -> void:
	_update_state()


func _on_export_pressed() -> void:
	if not _export_service:
		status_label.text = "Export service not available"
		return

	if _selected_candidate_id.is_empty():
		status_label.text = "No candidate selected"
		return

	if tileset_path_edit.text.is_empty():
		status_label.text = "TileSet path required"
		return

	var profile_idx: int = profile_selector.get_selected_id()
	var profile_names: PackedStringArray = [
		"top_down_default", "platformer_default", "debug_visualization"
	]
	var profile_name: String = profile_names[profile_idx]

	status_label.text = "Exporting %s..." % _selected_candidate_id
	export_btn.disabled = true

	_export_service.export_candidate(
		_result_path,
		_selected_candidate_id,
		tileset_path_edit.text,
		profile_name,
		export_folder_edit.text,
		export_name_edit.text,
	)


func _on_export_completed(candidate_id: String, success: bool, scene_path: String) -> void:
	if success:
		status_label.text = "Exported to %s" % scene_path
	else:
		status_label.text = "Export failed for %s" % candidate_id

	export_btn.disabled = false
	_update_state()


func _update_state() -> void:
	var can_export: bool = (
		not _selected_candidate_id.is_empty()
		and not tileset_path_edit.text.is_empty()
	)
	export_btn.disabled = not can_export

	if can_export:
		status_label.text = "Ready to export %s" % _selected_candidate_id
	else:
		status_label.text = "Select candidate and TileSet"
