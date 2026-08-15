extends Node

## Test suite for CompiledSchema and ValidationResult
## Tests core JSON Schema Draft 2020-12 validation keywords

var test_count: int = 0
var pass_count: int = 0
var fail_count: int = 0
var errors: Array[String] = []


func _ready() -> void:
	run_all_tests()
	print_summary()


# ============================================================================
# VALIDATION RESULT TESTS
# ============================================================================

func test_validation_result_success() -> void:
	test_count += 1
	var result := ValidationResult.new()
	assert(result.success == true, "ValidationResult should start with success=true")
	pass_count += 1


func test_validation_result_add_error() -> void:
	test_count += 1
	var result := ValidationResult.new()
	result.add_error("Test error")
	assert(result.success == false, "add_error should set success=false")
	assert(result.errors.size() == 1, "Should have one error")
	assert(result.errors[0] == "Test error", "Error message mismatch")
	pass_count += 1


func test_validation_result_add_error_with_path() -> void:
	test_count += 1
	var result := ValidationResult.new()
	result.add_error("Type mismatch", "$.properties.age")
	assert(result.success == false, "Should have failure status")
	assert("$.properties.age" in result.errors[0], "Error should contain path information")
	pass_count += 1


func test_validation_result_multiple_errors() -> void:
	test_count += 1
	var result := ValidationResult.new()
	result.add_error("Error 1")
	result.add_error("Error 2")
	result.add_error("Error 3")
	assert(result.errors.size() == 3, "Should have three errors")
	assert(result.success == false, "Should be failed status")
	pass_count += 1


func test_validation_result_to_dict() -> void:
	test_count += 1
	var result := ValidationResult.new()
	result.add_error("Test error", "$.test")
	var result_dict = result.to_dict()
	assert(result_dict.has("success"), "to_dict should have success key")
	assert(result_dict.has("error_count"), "to_dict should have error_count key")
	assert(result_dict.has("errors"), "to_dict should have errors key")
	assert(result_dict.has("path"), "to_dict should have path key")
	assert(result_dict["error_count"] == 1, "error_count should match")
	pass_count += 1


# ============================================================================
# TYPE VALIDATION TESTS
# ============================================================================

func test_type_validation_null() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "null"})
	var result = schema.validate(null)
	assert(result.success, "null should validate against type: null")
	pass_count += 1


func test_type_validation_boolean() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "boolean"})
	var result = schema.validate(true)
	assert(result.success, "true should validate against type: boolean")
	print_debug("Boolean validation passed")
	pass_count += 1


func test_type_validation_integer() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "integer"})
	var result = schema.validate(42)
	assert(result.success, "integer should validate against type: integer")
	pass_count += 1


func test_type_validation_number() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number"})
	var result = schema.validate(3.14)
	assert(result.success, "float should validate against type: number")
	pass_count += 1


func test_type_validation_string() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string"})
	var result = schema.validate("hello")
	assert(result.success, "string should validate against type: string")
	pass_count += 1


func test_type_validation_array() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "array"})
	var result = schema.validate([1, 2, 3])
	assert(result.success, "array should validate against type: array")
	pass_count += 1


func test_type_validation_object() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "object"})
	var result = schema.validate({"key": "value"})
	assert(result.success, "object should validate against type: object")
	pass_count += 1


func test_type_validation_reject_wrong_type() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string"})
	var result = schema.validate(42)
	if !result.success:
		pass_count += 1
		print_debug("Type validation rejection works: %s" % result.errors)
	else:
		fail_count += 1
		errors.append("Type validation should reject number when expecting string")


# ============================================================================
# NUMERIC BOUNDS TESTS
# ============================================================================

func test_minimum_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number", "minimum": 10.0})
	var result = schema.validate(15.0)
	assert(result.success, "15 should be >= 10")
	pass_count += 1


func test_minimum_boundary() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number", "minimum": 10.0})
	var result = schema.validate(10.0)
	assert(result.success, "10 should equal minimum 10")
	pass_count += 1


func test_minimum_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number", "minimum": 10.0})
	var result = schema.validate(5.0)
	if !result.success:
		pass_count += 1
		print_debug("Minimum validation rejection works")
	else:
		fail_count += 1
		errors.append("Should reject 5 when minimum is 10")


func test_maximum_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number", "maximum": 100.0})
	var result = schema.validate(50.0)
	assert(result.success, "50 should be <= 100")
	pass_count += 1


func test_maximum_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number", "maximum": 100.0})
	var result = schema.validate(150.0)
	if !result.success:
		pass_count += 1
		print_debug("Maximum validation rejection works")
	else:
		fail_count += 1
		errors.append("Should reject 150 when maximum is 100")


func test_exclusive_minimum() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number", "exclusiveMinimum": 0.0})
	var result = schema.validate(0.1)
	assert(result.success, "0.1 should be > 0 (exclusive)")
	pass_count += 1


func test_exclusive_maximum() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "number", "exclusiveMaximum": 100.0})
	var result = schema.validate(99.9)
	assert(result.success, "99.9 should be < 100 (exclusive)")
	pass_count += 1


# ============================================================================
# STRING VALIDATION TESTS
# ============================================================================

func test_min_length_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string", "minLength": 3})
	var result = schema.validate("hello")
	assert(result.success, "hello (5 chars) should be >= 3")
	pass_count += 1


func test_min_length_boundary() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string", "minLength": 3})
	var result = schema.validate("abc")
	assert(result.success, "abc (3 chars) should equal minLength 3")
	pass_count += 1


func test_min_length_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string", "minLength": 3})
	var result = schema.validate("ab")
	if !result.success:
		pass_count += 1
		print_debug("MinLength rejection works")
	else:
		fail_count += 1
		errors.append("Should reject string shorter than minLength")


func test_max_length_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string", "maxLength": 10})
	var result = schema.validate("hello")
	assert(result.success, "hello (5 chars) should be <= 10")
	pass_count += 1


func test_max_length_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string", "maxLength": 5})
	var result = schema.validate("hello world")
	if !result.success:
		pass_count += 1
		print_debug("MaxLength rejection works")
	else:
		fail_count += 1
		errors.append("Should reject string longer than maxLength")


func test_pattern_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string", "pattern": "^[a-z]+$"})
	var result = schema.validate("abc")
	if result.success:
		pass_count += 1
		print_debug("Pattern validation works")
	else:
		fail_count += 1
		errors.append("Pattern should match lowercase letters: %s" % result.errors)


func test_pattern_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"type": "string", "pattern": "^[0-9]+$"})
	var result = schema.validate("abc")
	if !result.success:
		pass_count += 1
		print_debug("Pattern rejection works")
	else:
		fail_count += 1
		errors.append("Should reject string not matching pattern")


# ============================================================================
# ENUM VALIDATION TESTS
# ============================================================================

func test_enum_string_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"enum": ["red", "green", "blue"]})
	var result = schema.validate("red")
	assert(result.success, "red should be in enum")
	pass_count += 1


func test_enum_number_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"enum": [1, 2, 3]})
	var result = schema.validate(2)
	assert(result.success, "2 should be in enum")
	pass_count += 1


func test_enum_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"enum": ["red", "green", "blue"]})
	var result = schema.validate("yellow")
	if !result.success:
		pass_count += 1
		print_debug("Enum rejection works")
	else:
		fail_count += 1
		errors.append("Should reject value not in enum")


func test_enum_mixed_types() -> void:
	test_count += 1
	var schema = CompiledSchema.new({"enum": [1, "two", null, true]})
	var result = schema.validate("two")
	assert(result.success, "Should accept mixed type in enum")
	pass_count += 1


# ============================================================================
# OBJECT PROPERTIES TESTS
# ============================================================================

func test_object_properties_basic() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {"type": "string"},
			"age": {"type": "integer"}
		}
	})
	var result = schema.validate({"name": "Alice", "age": 30})
	assert(result.success, "Valid object should pass")
	pass_count += 1


func test_object_required_fields() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {"type": "string"},
			"email": {"type": "string"}
		},
		"required": ["name", "email"]
	})
	var result = schema.validate({"name": "Alice"})
	if !result.success:
		pass_count += 1
		print_debug("Required field validation works")
	else:
		fail_count += 1
		errors.append("Should reject object missing required field")


func test_object_additional_properties_allowed() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {"type": "string"}
		},
		"additionalProperties": true
	})
	var result = schema.validate({"name": "Alice", "extra": "allowed"})
	assert(result.success, "additionalProperties: true should allow extra fields")
	pass_count += 1


func test_object_additional_properties_rejected() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {"type": "string"}
		},
		"additionalProperties": false
	})
	var result = schema.validate({"name": "Alice", "extra": "not allowed"})
	if !result.success:
		pass_count += 1
		print_debug("additionalProperties rejection works")
	else:
		fail_count += 1
		errors.append("Should reject additional properties when additionalProperties: false")


# ============================================================================
# ARRAY ITEMS TESTS
# ============================================================================

func test_array_items_schema() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "array",
		"items": {"type": "integer"}
	})
	var result = schema.validate([1, 2, 3])
	assert(result.success, "Array with all integers should validate")
	pass_count += 1


func test_array_items_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "array",
		"items": {"type": "string"}
	})
	var result = schema.validate([1, 2, 3])
	if !result.success:
		pass_count += 1
		print_debug("Array items type validation rejection works")
	else:
		fail_count += 1
		errors.append("Should reject array with wrong item types")


func test_array_min_items() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "array",
		"minItems": 2
	})
	var result = schema.validate([1, 2, 3])
	assert(result.success, "Array with 3 items should pass minItems: 2")
	pass_count += 1


func test_array_max_items() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "array",
		"maxItems": 2
	})
	var result = schema.validate([1, 2])
	assert(result.success, "Array with 2 items should pass maxItems: 2")
	pass_count += 1


func test_array_unique_items() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "array",
		"uniqueItems": true
	})
	var result = schema.validate([1, 2, 3])
	assert(result.success, "Array with unique items should pass")
	pass_count += 1


func test_array_unique_items_rejection() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "array",
		"uniqueItems": true
	})
	var result = schema.validate([1, 2, 2, 3])
	if !result.success:
		pass_count += 1
		print_debug("Unique items validation rejection works")
	else:
		fail_count += 1
		errors.append("Should reject array with duplicate items when uniqueItems: true")


# ============================================================================
# NESTED SCHEMA TESTS
# ============================================================================

func test_nested_object_schema() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"person": {
				"type": "object",
				"properties": {
					"name": {"type": "string"},
					"age": {"type": "integer"}
				}
			}
		}
	})
	var result = schema.validate({
		"person": {
			"name": "Alice",
			"age": 30
		}
	})
	assert(result.success, "Nested object should validate")
	pass_count += 1


func test_nested_array_schema() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "array",
		"items": {
			"type": "object",
			"properties": {
				"id": {"type": "integer"},
				"name": {"type": "string"}
			}
		}
	})
	var result = schema.validate([
		{"id": 1, "name": "First"},
		{"id": 2, "name": "Second"}
	])
	assert(result.success, "Array of objects should validate")
	pass_count += 1


func test_deeply_nested_schema() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"level1": {
				"type": "object",
				"properties": {
					"level2": {
						"type": "object",
						"properties": {
							"value": {"type": "string"}
						}
					}
				}
			}
		}
	})
	var result = schema.validate({
		"level1": {
			"level2": {
				"value": "deep"
			}
		}
	})
	assert(result.success, "Deeply nested object should validate")
	pass_count += 1


# ============================================================================
# COMBINATION TESTS (anyOf, oneOf, allOf, not)
# ============================================================================

func test_any_of_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"anyOf": [
			{"type": "string"},
			{"type": "number"}
		]
	})
	var result = schema.validate("hello")
	assert(result.success, "String should match anyOf with string or number")
	pass_count += 1


func test_one_of_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"oneOf": [
			{"type": "string", "minLength": 5},
			{"type": "number", "minimum": 10}
		]
	})
	var result = schema.validate("hello")
	assert(result.success, "Should validate with oneOf")
	pass_count += 1


func test_all_of_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"allOf": [
			{"type": "object", "properties": {"a": {"type": "string"}}},
			{"properties": {"b": {"type": "number"}}}
		]
	})
	var result = schema.validate({"a": "test", "b": 42})
	assert(result.success, "Should validate with allOf")
	pass_count += 1


func test_not_validation() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"not": {"type": "string"}
	})
	var result = schema.validate(42)
	assert(result.success, "Number should pass 'not string'")
	pass_count += 1


# ============================================================================
# REFERENCE RESOLUTION TESTS
# ============================================================================

func test_simple_ref() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"$defs": {
			"stringType": {"type": "string"}
		},
		"$ref": "#/$defs/stringType"
	})
	var result = schema.validate("hello")
	assert(result.success, "Should resolve simple $ref")
	pass_count += 1


func test_ref_in_properties() -> void:
	test_count += 1
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {
				"$defs": {
					"stringType": {"type": "string"}
				},
				"$ref": "#/$defs/stringType"
			}
		}
	})
	var result = schema.validate({"name": "Alice"})
	assert(result.success, "Should resolve $ref in properties")
	pass_count += 1


# ============================================================================
# TEST RUNNER
# ============================================================================

func run_all_tests() -> void:
	print("\n=== JSON Schema Validator Test Suite ===\n")

	# ValidationResult tests
	test_validation_result_success()
	test_validation_result_add_error()
	test_validation_result_add_error_with_path()
	test_validation_result_multiple_errors()
	test_validation_result_to_dict()

	# Type validation tests
	test_type_validation_null()
	test_type_validation_boolean()
	test_type_validation_integer()
	test_type_validation_number()
	test_type_validation_string()
	test_type_validation_array()
	test_type_validation_object()
	test_type_validation_reject_wrong_type()

	# Numeric bounds tests
	test_minimum_validation()
	test_minimum_boundary()
	test_minimum_rejection()
	test_maximum_validation()
	test_maximum_rejection()
	test_exclusive_minimum()
	test_exclusive_maximum()

	# String validation tests
	test_min_length_validation()
	test_min_length_boundary()
	test_min_length_rejection()
	test_max_length_validation()
	test_max_length_rejection()
	test_pattern_validation()
	test_pattern_rejection()

	# Enum validation tests
	test_enum_string_validation()
	test_enum_number_validation()
	test_enum_rejection()
	test_enum_mixed_types()

	# Object properties tests
	test_object_properties_basic()
	test_object_required_fields()
	test_object_additional_properties_allowed()
	test_object_additional_properties_rejected()

	# Array items tests
	test_array_items_schema()
	test_array_items_rejection()
	test_array_min_items()
	test_array_max_items()
	test_array_unique_items()
	test_array_unique_items_rejection()

	# Nested schema tests
	test_nested_object_schema()
	test_nested_array_schema()
	test_deeply_nested_schema()

	# Combination tests
	test_any_of_validation()
	test_one_of_validation()
	test_all_of_validation()
	test_not_validation()

	# Reference resolution tests
	test_simple_ref()
	test_ref_in_properties()


func print_summary() -> void:
	print("\n=== Test Summary ===")
	print("Total: %d" % test_count)
	print("Passed: %d" % pass_count)
	print("Failed: %d" % fail_count)

	if errors.size() > 0:
		print("\n=== Errors ===")
		for error in errors:
			print("  - %s" % error)

	if fail_count == 0:
		print("\nAll tests passed!")
	else:
		print("\nSome tests failed. See details above.")
