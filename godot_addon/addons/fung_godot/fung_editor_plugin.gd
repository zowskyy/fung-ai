@tool
extends EditorPlugin

class_name FungEditorPlugin

var dock: Control = null
var backend_client: Node = null


func _enter_tree() -> void:
	print("[Fung] Editor plugin loaded")

	# Create the backend client service
	backend_client = preload("res://addons/fung_godot/services/fung_backend_client.gd").new()
	backend_client.name = "FungBackendClient"
	add_child(backend_client)

	# Create the dock UI
	dock = preload("res://addons/fung_godot/ui/fung_dock.tscn").instantiate()
	add_control_to_dock(DOCK_SLOT_LEFT_BR, dock)


func _exit_tree() -> void:
	if dock:
		remove_control_from_docks(dock)
		dock.queue_free()

	if backend_client:
		backend_client.queue_free()

	print("[Fung] Editor plugin unloaded")
