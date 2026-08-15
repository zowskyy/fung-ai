extends SceneTree

var _passed: bool = true
var _test_count: int = 0
var _passed_count: int = 0


func _initialize() -> void:
	_test_canonicalize_basic()
	_test_canonicalize_object_sorting()
	_test_canonicalize_array()
	_test_canonicalize_nested()
	_test_canonicalize_strings()
	_test_canonical_hash()
	_test_hash_deterministic()
	_test_hash_sensitivity()
	_finish()


func _test_canonicalize_basic() -> void:
	_test("null", Rfc8785Canonicalizer.canonicalize(null), "null")
	_test("true", Rfc8785Canonicalizer.canonicalize(true), "true")
	_test("false", Rfc8785Canonicalizer.canonicalize(false), "false")
	_test("integer", Rfc8785Canonicalizer.canonicalize(42), "42")
	_test("float", Rfc8785Canonicalizer.canonicalize(3.14), "3.14")


func _test_canonicalize_object_sorting() -> void:
	var obj1 = {"z": 1, "a": 2, "m": 3}
	_test("object keys sorted", Rfc8785Canonicalizer.canonicalize(obj1), "{\"a\":2,\"m\":3,\"z\":1}")

	var obj2 = {"b": 1, "a": 2}
	_test("object keys alphabetical", Rfc8785Canonicalizer.canonicalize(obj2), "{\"a\":2,\"b\":1}")


func _test_canonicalize_array() -> void:
	var arr1: Array = [1, 2, 3]
	_test("simple array", Rfc8785Canonicalizer.canonicalize(arr1), "[1,2,3]")

	var arr2: Array = []
	_test("empty array", Rfc8785Canonicalizer.canonicalize(arr2), "[]")


func _test_canonicalize_nested() -> void:
	var nested = {
		"spawns": [
			{"y": 10, "x": 5},
			{"x": 8, "y": 4}
		],
		"config": {"z_order": 1, "name": "test"}
	}
	var expected = "{\"config\":{\"name\":\"test\",\"z_order\":1},\"spawns\":[{\"x\":5,\"y\":10},{\"x\":8,\"y\":4}]}"
	_test("nested structure", Rfc8785Canonicalizer.canonicalize(nested), expected)


func _test_canonicalize_strings() -> void:
	_test("simple string", Rfc8785Canonicalizer.canonicalize("hello"), "\"hello\"")
	_test("string with quotes", Rfc8785Canonicalizer.canonicalize("say \"hi\""), "\"say \\\"hi\\\"\"")
	_test("string with backslash", Rfc8785Canonicalizer.canonicalize("path\\to\\file"), "\"path\\\\to\\\\file\"")


func _test_canonical_hash() -> void:
	var hash = Rfc8785Canonicalizer.canonical_hash({"key": "value"})
	_test("hash is 64 chars", hash.length() == 64, true)
	_test("hash is hex", _is_valid_hex(hash), true)


func _test_hash_deterministic() -> void:
	var data = {"z": 1, "a": 2}
	var hash1 = Rfc8785Canonicalizer.canonical_hash(data)
	var hash2 = Rfc8785Canonicalizer.canonical_hash(data)
	_test("hash is deterministic", hash1 == hash2, true)


func _test_hash_sensitivity() -> void:
	var data1 = {"key": "value1"}
	var data2 = {"key": "value2"}
	var hash1 = Rfc8785Canonicalizer.canonical_hash(data1)
	var hash2 = Rfc8785Canonicalizer.canonical_hash(data2)
	_test("hash changes with data", hash1 != hash2, true)


func _test(name: String, actual: Variant, expected: Variant) -> void:
	_test_count += 1
	if actual == expected:
		_passed_count += 1
		print("PASS: %s" % name)
	else:
		_passed = false
		print("FAIL: %s" % name)
		print("  Expected: %s" % str(expected))
		print("  Got:      %s" % str(actual))


func _is_valid_hex(s: String) -> bool:
	if s.length() != 64:
		return false
	for char in s:
		if not char in "0123456789abcdef":
			return false
	return true


func _finish() -> void:
	print("\n=== Test Results ===")
	print("Passed: %d/%d" % [_passed_count, _test_count])
	if _passed:
		print("test_rfc8785_canonicalizer: PASS")
		quit(0)
	else:
		print("test_rfc8785_canonicalizer: FAIL")
		quit(1)
