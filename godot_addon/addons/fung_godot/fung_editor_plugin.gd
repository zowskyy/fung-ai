@tool
extends EditorPlugin

class_name FungEditorPlugin

var dock: Control = null
var backend_client: Node = null
var export_service: Node = null
var manifest_service: Node = null


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

	# Create the manifest service
	manifest_service = preload("res://addons/fung_godot/services/fung_manifest.gd").new()
	manifest_service.name = "FungManifest"
	add_child(manifest_service)

	# Create the dock UI. add_control_to_dock() is what actually adds this
	# node to the live tree and triggers its _ready() (instantiate() alone
	# does not) - so the dock's child tabs only exist after this call.
	# Service wiring must happen after, not before.
	dock = preload("res://addons/fung_godot/ui/fung_dock.tscn").instantiate()
	add_control_to_dock(DOCK_SLOT_LEFT_BR, dock)

	if dock:
		if dock.has_method("set_backend_client"):
			dock.set_backend_client(backend_client)
		if dock.has_method("set_export_service"):
			dock.set_export_service(export_service)
		if dock.has_method("set_manifest_service"):
			dock.set_manifest_service(manifest_service)

	if export_service and export_service.has_method("set_manifest_service"):
		export_service.set_manifest_service(manifest_service)


func _exit_tree() -> void:
	if dock:
		remove_control_from_docks(dock)
		dock.queue_free()

	if backend_client:
		backend_client.queue_free()

	if export_service:
		export_service.queue_free()

	if manifest_service:
		manifest_service.queue_free()

	print("[Fung] Editor plugin unloaded")
