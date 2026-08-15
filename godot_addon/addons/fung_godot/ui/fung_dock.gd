@tool
extends Control

class_name FungDock

var tab_container: TabContainer = null
var generate_tab: FungGenerateTab = null


func _ready() -> void:
	if not Engine.is_editor_hint():
		return

	print("[Fung Dock] Ready")
	tab_container = TabContainer.new()
	tab_container.anchor_right = 1.0
	tab_container.anchor_bottom = 1.0
	add_child(tab_container)

	# Add actual Generate tab
	generate_tab = preload("res://addons/fung_godot/ui/generate_tab.gd").new()
	generate_tab.name = "Generate"
	tab_container.add_child(generate_tab)
	tab_container.set_tab_title(0, "Generate")

	# Add placeholder tabs for other features
	_add_placeholder_tab("Environment", "Biome presets, offline defaults")
	_add_placeholder_tab("Candidates", "Browse generated candidates")
	_add_placeholder_tab("Export", "Export selected candidate to scene")
	_add_placeholder_tab("Library", "Saved recipes, history")


func set_backend_client(backend_client: FungBackendClient) -> void:
	"""Pass backend client to Generate tab."""
	if generate_tab:
		generate_tab.set_backend_client(backend_client)


func _add_placeholder_tab(tab_name: String, placeholder_text: String) -> void:
	"""Add a placeholder tab (for future implementation)."""
	var panel = PanelContainer.new()
	panel.name = tab_name

	var label = Label.new()
	label.text = "[%s]\n%s" % [tab_name, placeholder_text]
	label.add_theme_font_size_override("font_size", 14)
	panel.add_child(label)

	tab_container.add_child(panel)
	tab_container.set_tab_title(tab_container.get_child_count() - 1, tab_name)
