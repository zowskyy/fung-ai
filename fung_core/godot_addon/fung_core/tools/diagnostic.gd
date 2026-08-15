## Diagnostic file to trigger all Phase 9 compilation errors at once
## This helps identify cascading errors that only appear when all modules load

extends SceneTree

func _initialize() -> void:
	print("Importing Phase 9 modules...")

	# Try to instantiate all core Phase 9 classes
	var logger := FungLogger.new()
	print("✓ FungLogger loaded")

	var result := ValidationResult.new()
	print("✓ ValidationResult loaded")

	var schema_dict: Dictionary = {}
	var compiled := CompiledSchema.new(schema_dict)
	print("✓ CompiledSchema loaded")

	var asset := JsonSchemaAsset.new(schema_dict)
	print("✓ JsonSchemaAsset loaded")

	var node := SchemaNode.new()
	print("✓ SchemaNode loaded")

	var save_service := SaveService.new()
	print("✓ SaveService loaded")

	print("All Phase 9 modules loaded successfully!")
	quit(0)
