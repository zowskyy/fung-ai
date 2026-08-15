class_name SnapshotSerializer
extends RefCounted


func serialize(world_state: Dictionary, entities: Array, flags: Dictionary) -> Dictionary:
	var snapshot := {}
	var top_keys := ["entities", "flags", "world_state"]
	top_keys.sort()
	for key: String in top_keys:
		match key:
			"entities":
				var sorted_entities: Array = []
				for entity in entities:
					if entity is Dictionary:
						sorted_entities.append(_sort_dict_recursive(entity))
					else:
						sorted_entities.append(entity)
				snapshot["entities"] = sorted_entities
			"flags":
				snapshot["flags"] = _sort_dict_recursive(flags)
			"world_state":
				snapshot["world_state"] = _sort_dict_recursive(world_state)
	return snapshot


func to_json_string(snapshot: Dictionary) -> String:
	return JSON.stringify(snapshot)


# GDScript Dictionaries preserve insertion order and JSON.stringify does not
# re-sort keys, so every key at every nesting level must be inserted here in
# alphabetical order for identical states to always hash identically.
func _sort_dict_recursive(value):
	if value is Dictionary:
		var sorted := {}
		var keys: Array = value.keys()
		keys.sort()
		for key in keys:
			sorted[key] = _sort_dict_recursive(value[key])
		return sorted
	elif value is Array:
		var result: Array = []
		for item in value:
			result.append(_sort_dict_recursive(item))
		return result
	else:
		return value
