## Demonstration of JSON Schema validation in the cave_boss example.
##
## This module shows how to use the native GDScript JSON Schema engine
## to validate game data. It loads cave_world.json and validates it
## against the world.schema.json contract.
##
## Usage: Integrate into main.gd after loading JSON data.
## Example: var validator := SchemaValidationExample.new()
##          var result := validator.validate_world_data()

class_name SchemaValidationExample
extends RefCounted

const WORLD_SCHEMA_PATH := "res://contracts/world.schema.json"
const CAVE_WORLD_PATH := "res://examples/cave_boss/cave_world.json"

var _save_service := SaveService.new()


## Validate cave_world.json against the world schema.
## Returns a ValidationResult with success status and any validation errors.
func validate_world_data() -> ValidationResult:
	print("\n=== Schema Validation Example ===")
	print("Loading world data from: %s" % CAVE_WORLD_PATH)

	# Load the world data
	var world_data := _save_service.load_json(CAVE_WORLD_PATH)
	if world_data.is_empty():
		var result := ValidationResult.new()
		result.success = false
		result.add_error("Failed to load cave_world.json")
		return result

	print("✓ Loaded cave_world.json successfully")
	print("  - version: %s" % world_data.get("version", "N/A"))
	print("  - id: %s" % world_data.get("id", "N/A"))
	print("  - dimensions: %dx%d" % [world_data.get("width", 0), world_data.get("height", 0)])
	print("  - tile count: %d" % world_data.get("tiles", []).size())
	print("  - spawn points: %d" % world_data.get("spawns", []).size())

	# Load the schema
	print("\nLoading schema from: %s" % WORLD_SCHEMA_PATH)
	var schema_data := _save_service.load_json(WORLD_SCHEMA_PATH)
	if schema_data.is_empty():
		var result := ValidationResult.new()
		result.success = false
		result.add_error("Failed to load world.schema.json")
		return result

	print("✓ Loaded world.schema.json successfully")
	print("  - schema title: %s" % schema_data.get("title", "N/A"))
	print("  - required fields: %s" % schema_data.get("required", []))

	# Create schema asset and compile
	print("\nCompiling schema...")
	var schema_asset := JsonSchemaAsset.new(schema_data)
	var compiled_schema := schema_asset.get_compiled()
	print("✓ Schema compiled successfully")

	# Validate the data
	print("\nValidating world data against schema...")
	var result := compiled_schema.validate(world_data)

	if result.success:
		print("✅ VALIDATION PASSED")
		print("The cave_world.json data conforms to world.schema.json")
	else:
		print("❌ VALIDATION FAILED")
		print("Error count: %d" % result.errors.size())
		for error in result.errors:
			print("  - %s" % error)

	print("\n" + "=".repeat(34))
	return result


## Validate all example JSON files against their schemas.
## Returns a dictionary mapping file paths to ValidationResult objects.
func validate_all_examples() -> Dictionary:
	print("\n=== Comprehensive Schema Validation ===")
	var results := {}

	# Define all example files and their corresponding schemas
	var validations := [
		{
			"data_path": "res://examples/cave_boss/cave_world.json",
			"schema_path": "res://contracts/world.schema.json",
			"name": "World",
		},
		{
			"data_path": "res://examples/cave_boss/cave_boss_entity.json",
			"schema_path": "res://contracts/entity.schema.json",
			"name": "Entity",
		},
		{
			"data_path": "res://examples/cave_boss/cave_encounter.json",
			"schema_path": "res://contracts/encounter.schema.json",
			"name": "Encounter",
		},
		{
			"data_path": "res://examples/cave_boss/narrative_sequence.json",
			"schema_path": "res://contracts/narrative.schema.json",
			"name": "Narrative",
		},
		{
			"data_path": "res://examples/cave_boss/animation_manifest.json",
			"schema_path": "res://contracts/animation_manifest.schema.json",
			"name": "Animation Manifest",
		},
		{
			"data_path": "res://examples/cave_boss/project.json",
			"schema_path": "res://contracts/project.schema.json",
			"name": "Project",
		},
		{
			"data_path": "res://examples/cave_boss/replay.json",
			"schema_path": "res://contracts/replay.schema.json",
			"name": "Replay",
		},
	]

	var passed := 0
	var failed := 0

	for validation in validations:
		var data := _save_service.load_json(validation.data_path)
		var schema := _save_service.load_json(validation.schema_path)

		if data.is_empty() or schema.is_empty():
			var result := ValidationResult.new()
			result.success = false
			if data.is_empty():
				result.add_error("Failed to load data file: %s" % validation.data_path)
			if schema.is_empty():
				result.add_error("Failed to load schema file: %s" % validation.schema_path)
			results[validation["name"]] = result
			failed += 1
			continue

		var schema_asset := JsonSchemaAsset.new(schema)
		var result := schema_asset.validate(data)
		results[validation["name"]] = result

		if result.success:
			print("✅ %s validation passed" % validation["name"])
			passed += 1
		else:
			print("❌ %s validation failed (%d errors)" % [validation["name"], result.errors.size()])
			for error in result.errors:
				print("   - %s" % error)
			failed += 1

	print("\n" + "=".repeat(34))
	print("Results: %d passed, %d failed" % [passed, failed])

	return results


## Example: Get detailed information about the world schema structure.
## This demonstrates how to inspect schema metadata.
func print_schema_info() -> void:
	var schema_data := _save_service.load_json(WORLD_SCHEMA_PATH)
	if schema_data.is_empty():
		print("ERROR: Failed to load schema")
		return

	print("\n=== Schema Information ===")
	print("Title: %s" % schema_data.get("title", "N/A"))
	print("Description: %s" % schema_data.get("description", "N/A"))
	print("Type: %s" % schema_data.get("type", "N/A"))
	print("Schema URI: %s" % schema_data.get("$id", "N/A"))

	var required_fields = schema_data.get("required", [])
	print("\nRequired fields (%d):" % required_fields.size())
	for field in required_fields:
		print("  - %s" % field)

	var properties = schema_data.get("properties", {})
	print("\nDefined properties (%d):" % properties.size())
	for prop_name in properties.keys():
		var prop = properties[prop_name]
		var prop_type = prop.get("type", "N/A")
		var description = prop.get("description", "")
		print("  - %s: %s%s" % [prop_name, prop_type, " (%s)" % description if description else ""])

	print("===========================================================")  # 27 equals
