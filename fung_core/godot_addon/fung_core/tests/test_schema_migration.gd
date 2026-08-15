extends SceneTree

var _passed: bool = true
var _test_count: int = 0
var _passed_count: int = 0


func _initialize() -> void:
	_test_migration_add()
	_test_migration_remove()
	_test_migration_replace()
	_test_migration_copy()
	_test_migration_deep_structures()
	_test_integrity_verification()
	_test_multiple_operations()
	_finish()


func _test_migration_add() -> void:
	var data = {"name": "test"}
	var migration = SchemaMigration.new("1.0", "1.1", {
		"op": "add",
		"path": "/version",
		"value": "1.1"
	})
	var result = migration.apply(data)
	_test("add creates new field", result.has("version"), true)
	_test("add sets correct value", result.get("version"), "1.1")
	_test("add preserves original", result.get("name"), "test")


func _test_migration_remove() -> void:
	var data = {"name": "test", "deprecated": "old"}
	var migration = SchemaMigration.new("1.0", "1.1", {
		"op": "remove",
		"path": "/deprecated"
	})
	var result = migration.apply(data)
	_test("remove deletes field", result.has("deprecated"), false)
	_test("remove preserves other", result.get("name"), "test")


func _test_migration_replace() -> void:
	var data = {"status": "active"}
	var migration = SchemaMigration.new("1.0", "1.1", {
		"op": "replace",
		"path": "/status",
		"value": "inactive"
	})
	var result = migration.apply(data)
	_test("replace modifies value", result.get("status"), "inactive")


func _test_migration_copy() -> void:
	var data = {"source": "data", "target": null}
	var migration = SchemaMigration.new("1.0", "1.1", {
		"op": "copy",
		"from": "/source",
		"path": "/target"
	})
	var result = migration.apply(data)
	_test("copy duplicates value", result.get("target"), "data")
	_test("copy preserves source", result.get("source"), "data")


func _test_migration_deep_structures() -> void:
	var data = {
		"spawns": [
			{"x": 5, "y": 10},
			{"x": 8, "y": 4}
		]
	}
	var migration = SchemaMigration.new("1.0", "1.1", [
		{
			"op": "replace",
			"path": "/spawns/0/x",
			"value": 20
		},
		{
			"op": "add",
			"path": "/spawns/0/z",
			"value": 0
		}
	])
	var result = migration.apply(data)
	_test("nested replace works", result["spawns"][0]["x"], 20)
	_test("nested add works", result["spawns"][0]["z"], 0)
	_test("preserves other spawns", result["spawns"][1]["x"], 8)


func _test_integrity_verification() -> void:
	var original = {"key": "value"}
	var migration = SchemaMigration.new("1.0", "1.1", {
		"op": "add",
		"path": "/newkey",
		"value": "newvalue"
	})
	var migrated = migration.apply(original)

	var verified = migration.verify_integrity(original, migrated)
	_test("verify_integrity accepts valid migration", verified, true)

	# Test with tampered data
	migrated["key"] = "tampered"
	var tampered_result = migration.verify_integrity(original, migrated)
	_test("verify_integrity rejects tampered migration", tampered_result, false)


func _test_multiple_operations() -> void:
	var data = {
		"name": "old",
		"version": "1.0",
		"config": {"debug": true, "port": 8080}
	}
	var migration = SchemaMigration.new("1.0", "2.0", [
		{"op": "replace", "path": "/name", "value": "new"},
		{"op": "replace", "path": "/version", "value": "2.0"},
		{"op": "replace", "path": "/config/debug", "value": false},
		{"op": "add", "path": "/config/timeout", "value": 30}
	])
	var result = migration.apply(data)
	_test("multi-op: name changed", result["name"], "new")
	_test("multi-op: version changed", result["version"], "2.0")
	_test("multi-op: config debug changed", result["config"]["debug"], false)
	_test("multi-op: config timeout added", result["config"]["timeout"], 30)


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


func _finish() -> void:
	print("\n=== Test Results ===")
	print("Passed: %d/%d" % [_passed_count, _test_count])
	if _passed:
		print("test_schema_migration: PASS")
		quit(0)
	else:
		print("test_schema_migration: FAIL")
		quit(1)
