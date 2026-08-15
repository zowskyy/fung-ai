class_name SchemaMigration
extends RefCounted

## Handles schema version migrations with JSON Patch support (RFC 6902 subset).
## Supports add, remove, replace, and copy operations on JSON Pointer paths.
## Verifies data integrity using cryptographic hashes.

var from_version: String = ""
var to_version: String = ""
var patch: Dictionary = {}  # Array of patch operations
var _pre_migration_hash: String = ""
var _post_migration_hash: String = ""


func _init(p_from_version: String = "", p_to_version: String = "", p_patch: Dictionary = {}) -> void:
	from_version = p_from_version
	to_version = p_to_version
	patch = p_patch


## Apply the migration patch to data.
## Returns a new migrated dictionary without modifying the original.
func apply(data: Dictionary) -> Dictionary:
	# Store pre-migration hash for integrity verification
	_pre_migration_hash = Rfc8785Canonicalizer.canonical_hash(data)

	# Deep copy the data to avoid modifying the original
	var migrated = _deep_copy(data)

	# Apply each operation in the patch array
	if patch is Array:
		for operation in patch:
			if operation is Dictionary:
				migrated = _apply_operation(migrated, operation)
	elif patch is Dictionary and not patch.is_empty():
		# Single operation case
		migrated = _apply_operation(migrated, patch)

	# Store post-migration hash
	_post_migration_hash = Rfc8785Canonicalizer.canonical_hash(migrated)

	return migrated


## Verify data integrity by checking hash chain.
## Returns true if pre and post migration hashes are valid.
func verify_integrity(original: Dictionary, migrated: Dictionary) -> bool:
	var original_hash = Rfc8785Canonicalizer.canonical_hash(original)
	var migrated_hash = Rfc8785Canonicalizer.canonical_hash(migrated)

	# Verify the migration was actually applied
	if original_hash == migrated_hash:
		return false  # Migration didn't change the data

	# If we have stored hashes, verify they match
	if not _pre_migration_hash.is_empty() and _pre_migration_hash != original_hash:
		return false  # Original data was tampered with

	if not _post_migration_hash.is_empty() and _post_migration_hash != migrated_hash:
		return false  # Migrated data was tampered with

	return true


## Internal: apply a single JSON Patch operation.
static func _apply_operation(data: Dictionary, operation: Dictionary) -> Dictionary:
	var op_type = operation.get("op", "").to_lower()
	var path = operation.get("path", "")

	match op_type:
		"add":
			return _apply_add(data, path, operation.get("value"))
		"remove":
			return _apply_remove(data, path)
		"replace":
			return _apply_replace(data, path, operation.get("value"))
		"copy":
			var from_path = operation.get("from", "")
			return _apply_copy(data, from_path, path)
		_:
			push_error("Unknown patch operation: %s" % op_type)
			return data


## Internal: apply an "add" operation.
static func _apply_add(data: Dictionary, path: String, value: Variant) -> Dictionary:
	if path == "":
		# Replace root
		if value is Dictionary:
			return value
		return {"_value": value}

	var parts = _parse_json_pointer(path)
	if parts.is_empty():
		return data

	_set_at_path(data, parts, value)
	return data


## Internal: apply a "remove" operation.
static func _apply_remove(data: Dictionary, path: String) -> Dictionary:
	if path == "":
		return {}

	var parts = _parse_json_pointer(path)
	if parts.is_empty():
		return data

	if parts.size() == 1:
		var key = parts[0]
		if data.has(key):
			data.erase(key)
		return data

	# Navigate to parent and remove the final key
	var parent = _get_at_path(data, parts.slice(0, -1))
	if parent is Dictionary:
		var last_key = parts[-1]
		if parent.has(last_key):
			parent.erase(last_key)
	elif parent is Array:
		var index = int(parts[-1])
		if index >= 0 and index < parent.size():
			parent.remove_at(index)

	return data


## Internal: apply a "replace" operation.
static func _apply_replace(data: Dictionary, path: String, value: Variant) -> Dictionary:
	if path == "":
		if value is Dictionary:
			return value
		return {"_value": value}

	var parts = _parse_json_pointer(path)
	if parts.is_empty():
		return data

	_set_at_path(data, parts, value)
	return data


## Internal: apply a "copy" operation.
static func _apply_copy(data: Dictionary, from_path: String, to_path: String) -> Dictionary:
	var source_value = _get_value_at_path(data, from_path)
	if source_value == null:
		push_warning("Copy source path not found: %s" % from_path)
		return data

	# Deep copy the value
	var copied = _deep_copy(source_value)
	_set_at_path(data, _parse_json_pointer(to_path), copied)
	return data


## Internal: parse a JSON Pointer path into components.
## Handles URL decoding per RFC 6901.
static func _parse_json_pointer(path: String) -> Array:
	if path == "" or path == "/":
		return []

	var parts: Array[String] = []
	if path.begins_with("/"):
		path = path.substr(1)

	var tokens = path.split("/")
	for token in tokens:
		# Unescape ~0 and ~1 per RFC 6901
		token = token.replace("~1", "/")
		token = token.replace("~0", "~")
		parts.append(token)

	return parts


## Internal: get value at a JSON Pointer path.
static func _get_value_at_path(data: Variant, path: String) -> Variant:
	var parts = _parse_json_pointer(path)
	if parts.is_empty():
		return data
	return _get_at_path(data, parts)


## Internal: navigate to a value using path components.
static func _get_at_path(data: Variant, parts: Array) -> Variant:
	var current = data
	for part in parts:
		if current is Dictionary:
			if not current.has(part):
				return null
			current = current[part]
		elif current is Array:
			var index = int(part)
			if index < 0 or index >= current.size():
				return null
			current = current[index]
		else:
			return null
	return current


## Internal: set a value at a JSON Pointer path, creating intermediate structures.
static func _set_at_path(data: Dictionary, parts: Array, value: Variant) -> void:
	if parts.is_empty():
		return

	var current = data
	for i in range(parts.size() - 1):
		var part = parts[i]
		if current is Dictionary:
			if not current.has(part):
				# Determine if next part is array index
				var next_part = parts[i + 1]
				if next_part.is_valid_int():
					current[part] = []
				else:
					current[part] = {}
			current = current[part]
		elif current is Array:
			var index = int(part)
			while current.size() <= index:
				current.append(null)
			if current[index] == null:
				var next_part = parts[i + 1]
				if next_part.is_valid_int():
					current[index] = []
				else:
					current[index] = {}
			current = current[index]

	# Set the final value
	var last_key = parts[-1]
	if current is Dictionary:
		current[last_key] = value
	elif current is Array:
		var index = int(last_key)
		while current.size() <= index:
			current.append(null)
		current[index] = value


## Internal: deep copy a value (handles nested structures).
static func _deep_copy(value: Variant) -> Variant:
	if value is Dictionary:
		var copy: Dictionary = {}
		for key in value.keys():
			copy[key] = _deep_copy(value[key])
		return copy
	elif value is Array:
		var copy: Array = []
		for item in value:
			copy.append(_deep_copy(item))
		return copy
	else:
		return value
