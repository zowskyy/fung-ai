## JSON Schema conformance test runner.
##
## Validates that the native GDScript JSON Schema engine conforms to
## JSON Schema Draft 2020-12 specification and validates example data
## against the fung_core contract schemas.
##
## Usage: godot --headless --path fung_core -s tools/conformance_runner.gd
##
## Exit code: 0 if all conformance tests pass, 1 if any fail.

extends SceneTree

var _passed := 0
var _failed := 0
var _start_msec: int = 0
var _done := false


func _initialize() -> void:
	_start_msec = Time.get_ticks_msec()
	print("\n" + "=".repeat(70))
	print("JSON Schema Engine Conformance Test Suite")
	print("=".repeat(70))

	# Run all conformance tests
	_test_core_api()
	_test_validation_result()
	_test_schema_asset()
	_test_compiled_schema()
	_test_schema_node()
	_test_example_validations()

	# Print summary
	var elapsed_ms := Time.get_ticks_msec() - _start_msec
	print("\n" + "=".repeat(70))
	print("Conformance Summary: %d passed, %d failed (%.0fms)" % [_passed, _failed, elapsed_ms])
	print("=".repeat(70) + "\n")

	_done = true


## Test: Core API classes exist and are callable
func _test_core_api() -> void:
	print("\n[CORE API]")

	# JsonSchemaAsset should exist and instantiate
	var asset := JsonSchemaAsset.new()
	_assert(asset != null, "JsonSchemaAsset instantiation")
	_assert(asset.schema is Dictionary, "JsonSchemaAsset.schema is Dictionary")
	_pass("JsonSchemaAsset instantiation")

	# CompiledSchema should exist and instantiate
	var compiled := CompiledSchema.new({})
	_assert(compiled != null, "CompiledSchema instantiation")
	_pass("CompiledSchema instantiation")

	# SchemaNode should exist and extend Node
	var node := SchemaNode.new()
	_assert(node is Node, "SchemaNode extends Node")
	_assert(node.has_signal("validation_failed"), "SchemaNode has validation_failed signal")
	_pass("SchemaNode instantiation")


## Test: ValidationResult tracks errors correctly
func _test_validation_result() -> void:
	print("\n[VALIDATION RESULT]")

	var result := ValidationResult.new()
	_assert(result.success == true, "Default success is true")
	_assert(result.errors.size() == 0, "Default errors empty")
	_pass("ValidationResult initialization")

	# Add error without path
	result.add_error("Test error")
	_assert(not result.success, "Adding error sets success to false")
	_assert(result.errors.size() == 1, "Error added")
	_pass("Error tracking without path")

	# Add error with path
	result.add_error("Path error", "$.field")
	_assert(result.errors.size() == 2, "Multiple errors tracked")
	_assert("$.field" in result.errors[1], "Path included in error message")
	_pass("Error tracking with path")

	# Serialize to dictionary
	var dict := result.to_dict()
	_assert(dict.has("success"), "Serialized result has 'success'")
	_assert(dict.has("error_count"), "Serialized result has 'error_count'")
	_assert(dict.has("errors"), "Serialized result has 'errors'")
	_assert(dict["error_count"] == 2, "Error count correct")
	_pass("ValidationResult serialization")


## Test: JsonSchemaAsset storage and caching
func _test_schema_asset() -> void:
	print("\n[SCHEMA ASSET]")

	var schema_dict := {
		"type": "object",
		"properties": {
			"id": { "type": "string" },
			"value": { "type": "integer" }
		}
	}

	var asset := JsonSchemaAsset.new(schema_dict)
	_assert(asset.schema == schema_dict, "Schema stored correctly")
	_pass("Schema dictionary storage")

	# Compilation
	var compiled1 := asset.get_compiled()
	_assert(compiled1 is CompiledSchema, "get_compiled returns CompiledSchema")
	_pass("Schema compilation")

	# Caching
	var compiled2 := asset.get_compiled()
	_assert(compiled1 == compiled2, "Compiled schema cached")
	_pass("Schema caching")


## Test: CompiledSchema validation execution
func _test_compiled_schema() -> void:
	print("\n[COMPILED SCHEMA]")

	var schema := CompiledSchema.new({ "type": "object" })

	# Valid data (non-null object in Phase 9)
	var valid_result := schema.validate({"key": "value"})
	_assert(valid_result is ValidationResult, "validate() returns ValidationResult")
	_assert(valid_result.success == true, "Non-null object validates")
	_pass("Validation of valid data")

	# Invalid data (null in Phase 9)
	var invalid_result := schema.validate(null)
	_assert(not invalid_result.success, "Null data fails validation")
	_assert(invalid_result.errors.size() > 0, "Null generates error message")
	_pass("Validation of invalid data (null)")


## Test: SchemaNode signal and methods
func _test_schema_node() -> void:
	print("\n[SCHEMA NODE]")

	var schema_dict := { "type": "object" }
	var asset := JsonSchemaAsset.new(schema_dict)
	var node := SchemaNode.new(asset)

	# Manual validation without signal
	var result := node.validate({"test": "data"})
	_assert(result is ValidationResult, "validate() returns ValidationResult")
	_assert(result.success == true, "validate() works")
	_pass("SchemaNode.validate()")

	# is_valid without schema should fail gracefully
	var node_no_schema := SchemaNode.new()
	var empty_result := node_no_schema.validate({})
	_assert(not empty_result.success, "Validation without schema fails")
	_pass("SchemaNode error handling")


## Test: Validation of example data against contract schemas
func _test_example_validations() -> void:
	print("\n[EXAMPLE VALIDATIONS]")

	var save_service := SaveService.new()

	# Test world.json validation
	var world_data := save_service.load_json("res://examples/cave_boss/cave_world.json")
	var world_schema := save_service.load_json("res://contracts/world.schema.json")

	if not world_data.is_empty() and not world_schema.is_empty():
		var world_asset := JsonSchemaAsset.new(world_schema)
		var world_result := world_asset.validate(world_data)
		_assert(world_result is ValidationResult, "World validation returns result")
		if not world_result.success:
			_fail("World validation failed: %s" % ", ".join(world_result.errors))
		else:
			_pass("World data validation")
	else:
		_fail("World data/schema files not found")

	# Test entity validation
	var entity_data := save_service.load_json("res://examples/cave_boss/cave_boss_entity.json")
	var entity_schema := save_service.load_json("res://contracts/entity.schema.json")

	if not entity_data.is_empty() and not entity_schema.is_empty():
		var entity_asset := JsonSchemaAsset.new(entity_schema)
		var entity_result := entity_asset.validate(entity_data)
		_assert(entity_result is ValidationResult, "Entity validation returns result")
		if not entity_result.success:
			_fail("Entity validation failed: %s" % ", ".join(entity_result.errors))
		else:
			_pass("Entity data validation")
	else:
		_fail("Entity data/schema files not found")


# ============================================================================
# Test Utilities
# ============================================================================

func _assert(condition: bool, message: String) -> void:
	if not condition:
		_fail(message)


func _pass(message: String) -> void:
	_passed += 1
	print("  ✅ %s" % message)


func _fail(message: String) -> void:
	_failed += 1
	print("  ❌ %s" % message)


func _process(_delta: float) -> bool:
	if _done:
		quit(0 if _failed == 0 else 1)
		return true
	return false
