class_name ArchetypeDatabase
extends RefCounted

var _archetypes: Dictionary = {}


func register_archetype(archetype_id: String, defaults: Dictionary) -> void:
	_archetypes[archetype_id] = defaults


func get_archetype(archetype_id: String) -> Dictionary:
	return _archetypes.get(archetype_id, {})
