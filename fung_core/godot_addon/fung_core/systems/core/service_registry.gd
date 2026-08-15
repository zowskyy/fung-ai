class_name ServiceRegistry
extends RefCounted

var _services: Dictionary = {}


func register(name: String, service: Object) -> void:
	_services[name] = service


func get_service(name: String) -> Object:
	if not _services.has(name):
		push_error("ServiceRegistry: no service registered under name '%s'" % name)
		return null
	return _services[name]


func has_service(name: String) -> bool:
	return _services.has(name)
