class_name CompiledSchema
extends RefCounted

## A compiled JSON Schema Draft 2020-12 validator.
## Pre-parses and optimizes schema for efficient validation.

var _schema: Dictionary = {}
var _refs: Dictionary = {}


## Initialize with a schema dictionary.
func _init(schema: Dictionary) -> void:
	_schema = schema.duplicate(true)
	_compile_regex_patterns(_schema)
	_extract_refs(_schema)


## Pre-compile all regex patterns in the schema for better performance.
func _compile_regex_patterns(schema: Dictionary, path: String = "") -> void:
	if not schema is Dictionary:
		return

	for key in schema:
		var value = schema[key]

		if key == "pattern" and value is String:
			# Store compiled regex directly in the schema for easy access during validation
			var regex = RegEx.new()
			if regex.compile(value) != OK:
				push_error("Failed to compile regex pattern: %s" % value)
			else:
				schema["__compiled_pattern"] = regex

		# Recurse into nested objects
		if value is Dictionary:
			_compile_regex_patterns(value, path + "." + key if path else key)
		elif value is Array:
			for i in range(value.size()):
				if value[i] is Dictionary:
					_compile_regex_patterns(value[i], path + "." + key + "[%d]" % i if path else key + "[%d]" % i)


## Extract all $ref definitions for offline resolution.
func _extract_refs(schema: Dictionary, path: String = "") -> void:
	if not schema is Dictionary:
		return
	
	for key in schema:
		var value = schema[key]
		
		if key == "$ref" and value is String:
			_refs[value] = schema.duplicate(true)
		
		if value is Dictionary:
			_extract_refs(value, path + "." + key if path else key)
		elif value is Array:
			for i in range(value.size()):
				if value[i] is Dictionary:
					_extract_refs(value[i], path + "." + key + "[%d]" % i if path else key + "[%d]" % i)


## Main validation entry point.
func validate(data: Variant) -> ValidationResult:
	var result = ValidationResult.new()
	_validate_internal(data, _schema, "$", result)
	return result


## Internal recursive validation function.
func _validate_internal(data: Variant, schema: Dictionary, path: String, result: ValidationResult) -> void:
	# Handle $ref (offline inline references only)
	if schema.has("$ref"):
		var ref = schema["$ref"]
		if _refs.has(ref):
			_validate_internal(data, _refs[ref], path, result)
			return
	
	# Type validation
	if schema.has("type"):
		if not _validate_type(data, schema["type"], path, result):
			return
	
	# Const validation
	if schema.has("const"):
		if data != schema["const"]:
			result.add_error("Value must be %s" % [schema["const"]], path)
			return
	
	# Enum validation
	if schema.has("enum"):
		if not data in schema["enum"]:
			result.add_error("Value must be one of: %s" % [schema["enum"]], path)
			return
	
	# Numeric validations
	if data is int or data is float:
		if schema.has("minimum"):
			if data < schema["minimum"]:
				result.add_error("Value %s is less than minimum %s" % [data, schema["minimum"]], path)
		
		if schema.has("maximum"):
			if data > schema["maximum"]:
				result.add_error("Value %s is greater than maximum %s" % [data, schema["maximum"]], path)
	
	# String validations
	if data is String:
		if schema.has("minLength"):
			if data.length() < schema["minLength"]:
				result.add_error("String length %d is less than minLength %d" % [data.length(), schema["minLength"]], path)
		
		if schema.has("maxLength"):
			if data.length() > schema["maxLength"]:
				result.add_error("String length %d is greater than maxLength %d" % [data.length(), schema["maxLength"]], path)
		
		if schema.has("pattern"):
			if schema.has("__compiled_pattern"):
				var regex = schema["__compiled_pattern"]
				if not regex.search(data):
					result.add_error("String does not match pattern: %s" % [schema["pattern"]], path)
			else:
				# Fallback: compile on the fly if not pre-compiled
				var regex = RegEx.new()
				if regex.compile(schema["pattern"]) != OK:
					result.add_error("Failed to compile pattern: %s" % [schema["pattern"]], path)
				elif not regex.search(data):
					result.add_error("String does not match pattern: %s" % [schema["pattern"]], path)
	
	# Array validations
	if data is Array:
		if schema.has("items") and schema["items"] is Dictionary:
			for i in range(data.size()):
				var item_path := "%s[%d]" % [path, i]
				_validate_internal(data[i], schema["items"], item_path, result)
	
	# Object validations
	if data is Dictionary:
		# Validate required fields
		if schema.has("required") and schema["required"] is Array:
			for required_field in schema["required"]:
				if not data.has(required_field):
					result.add_error("Required field '%s' is missing" % [required_field], path)
		
		# Validate properties
		if schema.has("properties") and schema["properties"] is Dictionary:
			for prop_name in schema["properties"]:
				if data.has(prop_name):
					var prop_path := "%s.%s" % [path, prop_name]
					var prop_schema = schema["properties"][prop_name]
					if prop_schema is Dictionary:
						_validate_internal(data[prop_name], prop_schema, prop_path, result)
		
		# Check for additional properties
		if schema.has("additionalProperties"):
			if schema["additionalProperties"] == false:
				var allowed_props = {}
				if schema.has("properties"):
					allowed_props = schema["properties"].keys()
				
				for prop_name in data.keys():
					if not prop_name in allowed_props:
						result.add_error("Additional property '%s' is not allowed" % [prop_name], path)
			elif schema["additionalProperties"] is Dictionary:
				# Validate additional properties against the schema
				var allowed_props = {}
				if schema.has("properties"):
					allowed_props = schema["properties"].keys()
				
				for prop_name in data.keys():
					if not prop_name in allowed_props:
						var prop_path := "%s.%s" % [path, prop_name]
						_validate_internal(data[prop_name], schema["additionalProperties"], prop_path, result)


## Validate a value against a type specification.
func _validate_type(data: Variant, type_spec: Variant, path: String, result: ValidationResult) -> bool:
	if type_spec is String:
		return _validate_single_type(data, type_spec, path, result)
	elif type_spec is Array:
		# Multiple allowed types
		for type_name in type_spec:
			if _validate_single_type(data, type_name, path, result):
				return true
		
		result.add_error("Value type is not one of: %s" % [type_spec], path)
		return false
	
	return true


## Validate against a single type string.
func _validate_single_type(data: Variant, type_name: String, path: String, result: ValidationResult) -> bool:
	var data_type := typeof(data)
	
	match type_name:
		"null":
			return data == null
		"boolean":
			return data_type == TYPE_BOOL
		"object":
			return data_type == TYPE_DICTIONARY
		"array":
			return data_type == TYPE_ARRAY
		"number":
			return data_type == TYPE_INT or data_type == TYPE_FLOAT
		"integer":
			return data_type == TYPE_INT
		"string":
			return data_type == TYPE_STRING
		_:
			push_error("Unknown type: %s" % type_name)
			return false
