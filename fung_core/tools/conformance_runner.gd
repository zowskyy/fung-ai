#!/usr/bin/env godot -s

## Headless JSON Schema conformance test runner
## Loads conformance tests from JSON files and validates against schemas
## Exit code: 0 if all tests pass, 1 if any fail

extends SceneTree

var conformance_tests_dir: String = ""
var test_results: Dictionary = {
	"passed": 0,
	"failed": 0,
	"errors": []
}
var all_tests_completed: bool = false


func _initialize() -> void:
	# Determine the conformance tests directory
	var script_path = get_script().resource_path
	var script_dir = script_path.get_basename().get_basename()
	conformance_tests_dir = script_dir.get_basename() + "/godot_addon/fung_core/tests/conformance"

	# If not found, try relative to project root
	if !DirAccess.dir_exists_absolute(conformance_tests_dir):
		conformance_tests_dir = "res://tests/conformance"

	print("Conformance tests directory: %s" % conformance_tests_dir)
	run_conformance_tests()
	all_tests_completed = true


func run_conformance_tests() -> void:
	print("\n=== JSON Schema Conformance Test Runner ===\n")

	if !DirAccess.dir_exists_absolute(conformance_tests_dir):
		print("ERROR: Conformance tests directory not found: %s" % conformance_tests_dir)
		test_results["errors"].append("Conformance directory not found")
		return

	var dir = DirAccess.open(conformance_tests_dir)
	if dir == null:
		print("ERROR: Failed to open conformance directory")
		test_results["errors"].append("Failed to open directory")
		return

	# Find all JSON test files
	var test_files: Array = []
	dir.list_dir_begin()
	var file_name = dir.get_next()
	while file_name != "":
		if file_name.ends_with(".json"):
			test_files.append(file_name)
		file_name = dir.get_next()

	if test_files.is_empty():
		print("WARNING: No test files found in %s" % conformance_tests_dir)
		return

	# Run each test file
	for test_file in test_files:
		run_test_file(conformance_tests_dir + "/" + test_file)

	# Print summary
	print_test_summary()


func run_test_file(file_path: String) -> void:
	print("Loading test file: %s" % file_path.get_file())

	var json = JSON.new()
	var file = FileAccess.open(file_path, FileAccess.READ)
	if file == null:
		print("  ERROR: Could not open file")
		test_results["errors"].append("Could not open: %s" % file_path)
		return

	var content = file.get_as_text()
	var parse_error = json.parse(content)
	if parse_error != OK:
		print("  ERROR: Invalid JSON in file")
		test_results["errors"].append("Invalid JSON in: %s" % file_path)
		return

	var test_data = json.data
	if !test_data.has("tests"):
		print("  ERROR: Test file missing 'tests' array")
		test_results["errors"].append("Missing 'tests' in: %s" % file_path)
		return

	var tests = test_data["tests"]
	if tests is not Array:
		print("  ERROR: 'tests' is not an array")
		test_results["errors"].append("'tests' is not array in: %s" % file_path)
		return

	# Run each test in the file
	for test_case in tests:
		if test_case is not Dictionary:
			continue

		var schema_dict = test_case.get("schema", {})
		var data = test_case.get("data")
		var expected_valid = test_case.get("valid", false)
		var description = test_case.get("description", "")

		if schema_dict.is_empty():
			continue

		# Create compiled schema and validate
		var schema = CompiledSchema.new(schema_dict)
		var result = schema.validate(data)

		# Check result
		if result.success == expected_valid:
			test_results["passed"] += 1
			if description:
				print("  PASS: %s" % description)
			else:
				print("  PASS: Data %s validated as expected" % [data])
		else:
			test_results["failed"] += 1
			var msg = "  FAIL: %s (expected valid=%s, got valid=%s)" % [description, expected_valid, result.success]
			print(msg)
			if result.errors.size() > 0:
				for error in result.errors:
					print("    Error: %s" % error)
			test_results["errors"].append(msg)


func print_test_summary() -> void:
	print("\n=== Conformance Test Summary ===")
	print("Passed: %d" % test_results["passed"])
	print("Failed: %d" % test_results["failed"])

	if test_results["errors"].size() > 0:
		print("\n=== Errors ===")
		for error in test_results["errors"]:
			print("  %s" % error)

	print("")


func _process(_delta: float) -> bool:
	if all_tests_completed:
		if test_results["failed"] == 0:
			print("All conformance tests passed!")
			quit(0)
		else:
			print("Some conformance tests failed.")
			quit(1)
	return false
