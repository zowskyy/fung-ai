extends SceneTree

var _passed: bool = true
var _test_count: int = 0
var _pass_count: int = 0

const TIMEOUT_MSEC: int = 5000
var _start_msec: int = 0
var _done: bool = false


func _initialize() -> void:
	_start_msec = Time.get_ticks_msec()
	_run_tests()


func _run_tests() -> void:
	print("\n=== JSON Schema Validation Tests ===\n")
	
	_test_validation_result()
	_test_basic_types()
	_test_enum_validation()
	_test_const_validation()
	_test_numeric_bounds()
	_test_string_length()
	_test_pattern_validation()
	_test_array_items()
	_test_object_properties()
	_test_required_fields()
	_test_additional_properties()
	_test_nested_validation()
	
	_finish_tests()


func _test_validation_result() -> void:
	_assert_test("ValidationResult created")
	var result = ValidationResult.new()
	assert(result.success == true, "Initial success should be true")
	assert(result.errors.is_empty(), "Initial errors should be empty")
	
	_assert_test("ValidationResult.add_error")
	result.add_error("Test error", "$.test")
	assert(result.success == false, "Success should be false after adding error")
	assert(result.errors.size() == 1, "Should have one error")
	assert("Test error" in result.errors[0], "Error message should contain test error text")
	
	_assert_test("ValidationResult.to_dict()")
	var dict = result.to_dict()
	assert(dict.has("success"), "to_dict should have 'success' key")
	assert(dict.has("error_count"), "to_dict should have 'error_count' key")
	assert(dict.has("errors"), "to_dict should have 'errors' key")
	assert(dict["error_count"] == 1, "error_count should be 1")


func _test_basic_types() -> void:
	_assert_test("CompiledSchema compiles without errors")
	var simple_schema = {"type": "string"}
	var schema = CompiledSchema.new(simple_schema)
	assert(schema != null, "Schema should compile successfully")
	
	_assert_test("Type: string validation passes")
	var result = schema.validate("hello")
	assert(result.success, "String validation should pass: %s" % result.errors)
	
	_assert_test("Type: string validation fails for integer")
	result = schema.validate(42)
	assert(!result.success, "String validation should fail for integer")
	assert(result.errors.size() > 0, "Should have error message")
	
	_assert_test("Type: integer validation")
	schema = CompiledSchema.new({"type": "integer"})
	result = schema.validate(42)
	assert(result.success, "Integer validation should pass")
	result = schema.validate(42.5)
	assert(!result.success, "Integer validation should fail for float")
	
	_assert_test("Type: number validation")
	schema = CompiledSchema.new({"type": "number"})
	result = schema.validate(42)
	assert(result.success, "Number validation should pass for integer")
	result = schema.validate(42.5)
	assert(result.success, "Number validation should pass for float")
	result = schema.validate("42")
	assert(!result.success, "Number validation should fail for string")
	
	_assert_test("Type: boolean validation")
	schema = CompiledSchema.new({"type": "boolean"})
	result = schema.validate(true)
	assert(result.success, "Boolean validation should pass")
	result = schema.validate(false)
	assert(result.success, "Boolean validation should pass for false")
	result = schema.validate(1)
	assert(!result.success, "Boolean validation should fail for integer")
	
	_assert_test("Type: array validation")
	schema = CompiledSchema.new({"type": "array"})
	result = schema.validate([1, 2, 3])
	assert(result.success, "Array validation should pass")
	result = schema.validate({})
	assert(!result.success, "Array validation should fail for object")
	
	_assert_test("Type: object validation")
	schema = CompiledSchema.new({"type": "object"})
	result = schema.validate({})
	assert(result.success, "Object validation should pass")
	result = schema.validate([])
	assert(!result.success, "Object validation should fail for array")
	
	_assert_test("Type: null validation")
	schema = CompiledSchema.new({"type": "null"})
	result = schema.validate(null)
	assert(result.success, "Null validation should pass")
	result = schema.validate("not null")
	assert(!result.success, "Null validation should fail for non-null")


func _test_enum_validation() -> void:
	_assert_test("Enum validation with allowed value")
	var schema = CompiledSchema.new({"enum": ["red", "green", "blue"]})
	var result = schema.validate("red")
	assert(result.success, "Enum validation should pass for allowed value")
	
	_assert_test("Enum validation with disallowed value")
	result = schema.validate("yellow")
	assert(!result.success, "Enum validation should fail for disallowed value")
	assert(result.errors.size() > 0, "Should have error message")


func _test_const_validation() -> void:
	_assert_test("Const validation with matching value")
	var schema = CompiledSchema.new({"const": 42})
	var result = schema.validate(42)
	assert(result.success, "Const validation should pass for matching value")
	
	_assert_test("Const validation with non-matching value")
	result = schema.validate(43)
	assert(!result.success, "Const validation should fail for non-matching value")


func _test_numeric_bounds() -> void:
	_assert_test("Minimum validation passes")
	var schema = CompiledSchema.new({"type": "number", "minimum": 10})
	var result = schema.validate(15)
	assert(result.success, "Minimum validation should pass for value >= minimum")
	
	_assert_test("Minimum validation fails")
	result = schema.validate(5)
	assert(!result.success, "Minimum validation should fail for value < minimum")
	
	_assert_test("Maximum validation passes")
	schema = CompiledSchema.new({"type": "number", "maximum": 100})
	result = schema.validate(50)
	assert(result.success, "Maximum validation should pass for value <= maximum")
	
	_assert_test("Maximum validation fails")
	result = schema.validate(150)
	assert(!result.success, "Maximum validation should fail for value > maximum")


func _test_string_length() -> void:
	_assert_test("MinLength validation passes")
	var schema = CompiledSchema.new({"type": "string", "minLength": 3})
	var result = schema.validate("hello")
	assert(result.success, "MinLength validation should pass")
	
	_assert_test("MinLength validation fails")
	result = schema.validate("hi")
	assert(!result.success, "MinLength validation should fail")
	
	_assert_test("MaxLength validation passes")
	schema = CompiledSchema.new({"type": "string", "maxLength": 5})
	result = schema.validate("hello")
	assert(result.success, "MaxLength validation should pass")
	
	_assert_test("MaxLength validation fails")
	result = schema.validate("toolong")
	assert(!result.success, "MaxLength validation should fail")


func _test_pattern_validation() -> void:
	_assert_test("Pattern validation passes")
	var schema = CompiledSchema.new({"type": "string", "pattern": "^[a-z]+$"})
	var result = schema.validate("abc")
	assert(result.success, "Pattern validation should pass: %s" % result.errors)
	
	_assert_test("Pattern validation fails")
	result = schema.validate("ABC123")
	assert(!result.success, "Pattern validation should fail for non-matching pattern")


func _test_array_items() -> void:
	_assert_test("Array items validation")
	var schema = CompiledSchema.new({
		"type": "array",
		"items": {"type": "string"}
	})
	var result = schema.validate(["a", "b", "c"])
	assert(result.success, "Array items validation should pass: %s" % result.errors)
	
	_assert_test("Array items validation fails")
	result = schema.validate(["a", 2, "c"])
	assert(!result.success, "Array items validation should fail with mixed types")


func _test_object_properties() -> void:
	_assert_test("Object properties validation")
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {"type": "string"},
			"age": {"type": "integer"}
		}
	})
	var result = schema.validate({"name": "John", "age": 30})
	assert(result.success, "Object properties validation should pass: %s" % result.errors)
	
	_assert_test("Object properties validation with type error")
	result = schema.validate({"name": "John", "age": "30"})
	assert(!result.success, "Object properties validation should fail with wrong type")


func _test_required_fields() -> void:
	_assert_test("Required fields validation passes")
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {"type": "string"}
		},
		"required": ["name"]
	})
	var result = schema.validate({"name": "John"})
	assert(result.success, "Required fields validation should pass")
	
	_assert_test("Required fields validation fails")
	result = schema.validate({})
	assert(!result.success, "Required fields validation should fail when required field is missing")


func _test_additional_properties() -> void:
	_assert_test("AdditionalProperties false rejects extra fields")
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"name": {"type": "string"}
		},
		"additionalProperties": false
	})
	var result = schema.validate({"name": "John", "extra": "field"})
	assert(!result.success, "Should reject additional properties: %s" % result.errors)
	
	_assert_test("AdditionalProperties false accepts only defined properties")
	result = schema.validate({"name": "John"})
	assert(result.success, "Should accept defined properties only")


func _test_nested_validation() -> void:
	_assert_test("Nested object validation")
	var schema = CompiledSchema.new({
		"type": "object",
		"properties": {
			"person": {
				"type": "object",
				"properties": {
					"name": {"type": "string"},
					"age": {"type": "integer"}
				},
				"required": ["name"]
			}
		},
		"required": ["person"]
	})
	var result = schema.validate({
		"person": {
			"name": "John",
			"age": 30
		}
	})
	assert(result.success, "Nested object validation should pass: %s" % result.errors)
	
	_assert_test("Nested object validation fails on missing required field")
	result = schema.validate({
		"person": {
			"age": 30
		}
	})
	assert(!result.success, "Nested object validation should fail when nested required field is missing")


func _assert_test(test_name: String) -> void:
	_test_count += 1
	print("  [%d] %s" % [_test_count, test_name])


func _finish_tests() -> void:
	_pass_count = _test_count
	print("\n=== Test Summary ===")
	print("Total: %d" % _test_count)
	print("Passed: %d" % _pass_count)
	
	_finish()


func _process(_delta: float) -> bool:
	if _done:
		return true
	if Time.get_ticks_msec() - _start_msec > TIMEOUT_MSEC:
		push_error("test_json_schema timed out")
		_passed = false
		_finish()
		return true
	return false


func _finish() -> void:
	if _done:
		return
	_done = true
	if _passed:
		print("test_json_schema: PASS")
		quit(0)
	else:
		print("test_json_schema: FAIL")
		quit(1)
