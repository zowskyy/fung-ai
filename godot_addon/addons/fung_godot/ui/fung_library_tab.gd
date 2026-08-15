@tool
extends Control

class_name FungLibraryTab

# Library tab: browse reproducibility manifests written by past exports,
# and request a regenerate of the Generate tab from one of them.
# Builds its own child controls in code (no backing .tscn), same as the
# other tabs.

signal manifest_regenerate_requested(recipe_id: String, seed: int, map_size_tiles: Array)

var _manifest_service: FungManifest = null
var _manifests: Array[Dictionary] = []
var _selected_idx: int = -1

var manifest_list: ItemList
var refresh_btn: Button
var regenerate_btn: Button
var status_label: Label


func _ready() -> void:
	_build_ui()
	_setup_signals()


func set_manifest_service(manifest_service: FungManifest) -> void:
	# Set reference to manifest service and load its current contents.
	_manifest_service = manifest_service
	_refresh_manifests()


func _build_ui() -> void:
	var layout: VBoxContainer = VBoxContainer.new()
	layout.name = "Layout"
	layout.anchor_right = 1.0
	layout.anchor_bottom = 1.0
	add_child(layout)

	var manifests_header: HBoxContainer = HBoxContainer.new()
	manifests_header.name = "ManifestsHeader"
	layout.add_child(manifests_header)

	var manifests_title: Label = Label.new()
	manifests_title.name = "ManifestsTitle"
	manifests_title.text = "Exported Manifests"
	manifests_header.add_child(manifests_title)

	refresh_btn = Button.new()
	refresh_btn.name = "RefreshBtn"
	refresh_btn.text = "Refresh"
	manifests_header.add_child(refresh_btn)

	manifest_list = ItemList.new()
	manifest_list.name = "ManifestList"
	manifest_list.custom_minimum_size = Vector2(0, 160)
	layout.add_child(manifest_list)

	regenerate_btn = Button.new()
	regenerate_btn.name = "RegenerateBtn"
	regenerate_btn.text = "Regenerate from manifest"
	regenerate_btn.disabled = true
	layout.add_child(regenerate_btn)

	status_label = Label.new()
	status_label.name = "StatusLabel"
	status_label.text = "No manifests loaded"
	layout.add_child(status_label)

	layout.add_child(_build_placeholder_section(
		"Saved Recipes",
		"Not yet implemented - there is no recipe-saving backend yet."
	))
	layout.add_child(_build_placeholder_section(
		"Pinned Candidates",
		"Not yet implemented - there is no candidate-pinning backend yet."
	))


func _build_placeholder_section(title: String, placeholder_text: String) -> PanelContainer:
	# Same placeholder style as fung_dock.gd's _add_placeholder_tab(), but
	# embedded inline as a section rather than a whole tab.
	var panel: PanelContainer = PanelContainer.new()
	panel.name = title.replace(" ", "")

	var label: Label = Label.new()
	label.text = "[%s]\n%s" % [title, placeholder_text]
	label.add_theme_font_size_override("font_size", 14)
	panel.add_child(label)

	return panel


func _setup_signals() -> void:
	refresh_btn.pressed.connect(_on_refresh_pressed)
	manifest_list.item_selected.connect(_on_manifest_selected)
	regenerate_btn.pressed.connect(_on_regenerate_pressed)


func _on_refresh_pressed() -> void:
	_refresh_manifests()


func _refresh_manifests() -> void:
	manifest_list.clear()
	_selected_idx = -1
	regenerate_btn.disabled = true

	if not _manifest_service:
		status_label.text = "Manifest service not available"
		return

	_manifests = _manifest_service.list_manifests()

	if _manifests.is_empty():
		status_label.text = "No manifests found - export a candidate to create one"
		return

	for manifest in _manifests:
		var recipe_id: String = manifest.get("recipe_id", "unknown")
		var seed: int = int(manifest.get("seed", 0))
		var created_utc: String = manifest.get("created_utc", "")
		manifest_list.add_item("%s | seed %d | %s" % [recipe_id, seed, created_utc])

	status_label.text = "%d manifest(s) loaded" % _manifests.size()


func _on_manifest_selected(index: int) -> void:
	_selected_idx = index
	regenerate_btn.disabled = index < 0 or index >= _manifests.size()


func _on_regenerate_pressed() -> void:
	if _selected_idx < 0 or _selected_idx >= _manifests.size():
		return

	var manifest: Dictionary = _manifests[_selected_idx]
	var recipe_id: String = manifest.get("recipe_id", "")
	var seed: int = int(manifest.get("seed", 0))
	var map_size_tiles: Array = manifest.get("map_size_tiles", [96, 96])

	manifest_regenerate_requested.emit(recipe_id, seed, map_size_tiles)
	status_label.text = "Requested regenerate: %s (seed %d)" % [recipe_id, seed]
