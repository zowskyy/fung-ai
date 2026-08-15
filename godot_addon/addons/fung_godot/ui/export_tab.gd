@tool
extends Control

class_name FungExportTab

## Export tab: select TileSet, profile, and export settings.

signal export_requested(
	result_path: String,
	candidate_id: String,
	tileset_path: String,
	export_profile: String,
)

var _export_service: FungExportService = null
var _selected_candidate_id: String = ""
var _result_path: String = ""

@onready var tileset_selector: LineEdit = $TileSetContainer/TileSetPath
@onready var browse_btn: Button = $TileSetContainer/BrowseBtn
@onready var profile_selector: OptionButton = $ProfileContainer/ProfileSelector
@onready var export_name_edit: LineEdit = $ExportNameContainer/NameEdit
@onready var export_folder: LineEdit = $ExportFolderContainer/FolderEdit
@onready var layer_toggles_container: VBoxContainer = $LayerToggles
@onready var export_btn: Button = $ExportBtn
@onready var status_label: Label = $StatusLabel


func _ready() -> void:
	if not Engine.is_editor_hint():
		return

	_setup_ui()
	_setup_signals()
	_update_state()


func set_export_service(export_service: FungExportService) -> void:
	"""Set reference to export service."""
	_export_service = export_service
	if _export_service:
		_export_service.export_completed.connect(_on_export_completed)


func set_selected_candidate(candidate_id: String, result_path: String) -> void:
	"""Set the candidate to export."""
	_selected_candidate_id = candidate_id
	_result_path = result_path

	export_name_edit.text = candidate_id
	_update_state()


func _setup_ui() -> void:
	"""Initialize UI controls."""
	# Profile selector
	profile_selector.add_item("Top-Down (Default)", 0)
	profile_selector.add_item("Platformer (Default)", 1)
	profile_selector.add_item("Debug Visualization", 2)
	profile_selector.select(0)

	# Export name
	export_name_edit.text = "generated_level"
	export_name_edit.placeholder_text = "Scene name (no extension)"

	# Export folder
	export_folder.text = "res://generated/fung/levels"
	export_folder.placeholder_text = "res://... or user://..."

	# Layer toggles (for future expansion)
	var layer_names: PackedStringArray = ["Terrain", "Collision", "Navigation", "Preview"]
	for layer_name in layer_names:
		var hbox: HBoxContainer = HBoxContainer.new()
		var check: CheckBox = CheckBox.new()
		check.button_pressed = true
		check.text = layer_name
		hbox.add_child(check)
		layer_toggles_container.add_child(hbox)

	export_btn.disabled = true


func _setup_signals() -> void:
	"""Connect control signals."""
	browse_btn.pressed.connect(_on_browse_tileset)
	export_btn.pressed.connect(_on_export_pressed)
	tileset_selector.text_changed.connect(_on_tileset_changed)


func _on_browse_tileset() -> void:
	"""Browse for TileSet resource (placeholder)."""
	status_label.text = "TileSet browser not yet implemented"


func _on_tileset_changed(_new_text: String) -> void:
	"""Update export button state when tileset changes."""
	_update_state()


func _on_export_pressed() -> void:
	"""Start export with current settings."""
	if not _export_service:
		status_label.text = "Export service not available"
		return

	if _selected_candidate_id.is_empty():
		status_label.text = "No candidate selected"
		return

	if tileset_selector.text.is_empty():
		status_label.text = "TileSet path required"
		return

	var profile_idx: int = profile_selector.get_selected_id()
	var profile_name: String = ["top_down_default", "platformer_default", "debug_visualization"][
		profile_idx
	]

	status_label.text = "Exporting %s..." % _selected_candidate_id
	export_btn.disabled = true

	_export_service.export_candidate(
		_result_path,
		_selected_candidate_id,
		tileset_selector.text,
		profile_name,
	)


func _on_export_completed(candidate_id: String, success: bool, scene_path: String) -> void:
	"""Handle export completion."""
	if success:
		status_label.text = "Exported to %s" % scene_path
	else:
		status_label.text = "Export failed for %s" % candidate_id

	export_btn.disabled = false
	_update_state()


func _update_state() -> void:
	"""Update UI state based on selections."""
	var can_export: bool = (
		not _selected_candidate_id.is_empty()
		and not tileset_selector.text.is_empty()
	)
	export_btn.disabled = not can_export

	if can_export:
		status_label.text = "Ready to export %s" % _selected_candidate_id
	else:
		status_label.text = "Select candidate and TileSet"
