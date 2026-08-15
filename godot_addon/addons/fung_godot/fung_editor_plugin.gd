@tool
extends EditorPlugin

class_name FungEditorPlugin

var dock: Control = null
var backend_client: Node = null
var export_service: Node = null


func _enter_tree() -> void:
	print("[Fung] Editor plugin loaded")

	# Create the backend client service
	backend_client = preload("res://addons/fung_godot/services/fung_backend_client.gd").new()
	backend_client.name = "FungBackendClient"
	add_child(backend_client)

	# Create the export service
	export_service = preload("res://addons/fung_godot/services/fung_export_service.gd").new()
	export_service.name = "FungExportService"
	add_child(export_service)

	# Create the dock UI
	dock = preload("res://addons/fung_godot/ui/fung_dock.tscn").instantiate()
	if dock:
		# Connect services to dock
		if dock.has_method("set_backend_client"):
			dock.set_backend_client(backend_client)
		if dock.has_method("set_export_service"):
			dock.set_export_service(export_service)

	add_control_to_dock(DOCK_SLOT_LEFT_BR, dock)


func _exit_tree() -> void:
	if dock:
		remove_control_from_docks(dock)
		dock.queue_free()

	if backend_client:
		backend_client.queue_free()

	if export_service:
		export_service.queue_free()

	print("[Fung] Editor plugin unloaded")
