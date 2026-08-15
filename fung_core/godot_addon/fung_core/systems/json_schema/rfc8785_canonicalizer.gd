class_name Rfc8785Canonicalizer
extends RefCounted

## Implements RFC 8785 JSON canonicalization for deterministic hashing and verification.
## All object keys are sorted lexicographically and whitespace is minimized.
## This ensures identical data produces identical canonical JSON.


## Canonicalize a value according to RFC 8785 rules.
## Returns a deterministic JSON string suitable for hashing.
static func canonicalize(data: Variant) -> String:
	return _canonicalize_value(data)


## Generate a SHA-256 hash of the canonical form.
## Returns a 64-character hex string.
static func canonical_hash(data: Variant) -> String:
	var canonical := canonicalize(data)
	var bytes = canonical.to_utf8_buffer()
	return _sha256_hex(bytes)


## Internal: recursively canonicalize a value.
static func _canonicalize_value(value: Variant) -> String:
	if value is Dictionary:
		return _canonicalize_object(value)
	elif value is Array:
		return _canonicalize_array(value)
	elif value is String:
		return _canonicalize_string(value)
	elif value is bool:
		return "true" if value else "false"
	elif value is int or value is float:
		# JSON.stringify returns numbers directly without quotes
		return str(value)
	elif value == null:
		return "null"
	else:
		# For unknown types, convert to string representation
		return _canonicalize_string(str(value))


## Internal: canonicalize an object (Dictionary).
## Keys are sorted lexicographically, no whitespace added.
static func _canonicalize_object(obj: Dictionary) -> String:
	if obj.is_empty():
		return "{}"

	var keys: Array = obj.keys()
	keys.sort()

	var parts: Array[String] = []
	for key in keys:
		var canonical_key = _canonicalize_string(str(key))
		var canonical_value = _canonicalize_value(obj[key])
		parts.append(canonical_key + ":" + canonical_value)

	return "{" + ",".join(parts) + "}"


## Internal: canonicalize an array.
## Array elements maintain order, no extra whitespace.
static func _canonicalize_array(arr: Array) -> String:
	if arr.is_empty():
		return "[]"

	var parts: Array[String] = []
	for item in arr:
		parts.append(_canonicalize_value(item))

	return "[" + ",".join(parts) + "]"


## Internal: canonicalize a string with proper escaping.
## Escapes special characters and uses Unicode escape sequences for control chars.
static func _canonicalize_string(str_value: String) -> String:
	var result := "\""

	for char_code in str_value.unicode_at_pos(0) if str_value.length() == 1 else str_value.unicode_at_pos(0):
		# Process each character
		pass

	# Use a simpler approach: iterate through the string
	var i := 0
	while i < str_value.length():
		var char = str_value[i]
		var char_code = str_value.unicode_at(i)

		match char:
			'"':
				result += "\\\""
			'\\':
				result += "\\\\"
			'\b':
				result += "\\b"
			'\f':
				result += "\\f"
			'\n':
				result += "\\n"
			'\r':
				result += "\\r"
			'\t':
				result += "\\t"
			_:
				# Check if character needs Unicode escaping (control chars < 0x20)
				if char_code < 0x20:
					result += "\\u%04x" % char_code
				else:
					result += char
		i += 1

	result += "\""
	return result


## Internal: compute SHA-256 hash of bytes and return as hex string.
static func _sha256_hex(data: PackedByteArray) -> String:
	var hash = data.sha256_buffer()
	var hex := ""
	for byte in hash:
		hex += "%02x" % byte
	return hex
