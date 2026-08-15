@tool
extends Control

class_name FungDock

var tab_container: TabContainer = null


func _ready() -> void:
	print("[Fung Dock] Ready")
	tab_container = TabContainer.new()
	tab_container.anchor_right = 1.0
	tab_container.anchor_bottom = 1.0
	add_child(tab_container)

	# Add placeholder tabs
	_add_tab("Generate", "Seed, recipe, generate button")
	_add_tab("Environment", "Biome presets, offline defaults")
	_add_tab("Candidates", "Browse generated candidates")
	_add_tab("Export", "Export selected candidate to scene")
	_add_tab("Library", "Saved recipes, history")


func _add_tab(tab_name: String, placeholder_text: String) -> void:
	var panel = PanelContainer.new()
	panel.name = tab_name

	var label = Label.new()
	label.text = "[%s]\n%s" % [tab_name, placeholder_text]
	label.add_theme_font_size_override("font_size", 14)
	panel.add_child(label)

	tab_container.add_child(panel)
	tab_container.set_tab_title(tab_container.get_child_count() - 1, tab_name)
