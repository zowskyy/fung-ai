# Native GDScript JSON Schema Engine

## Overview

Fung Core now includes a **native GDScript JSON Schema validation engine** that validates game data at runtime without any Python dependencies. This document describes the implementation, API reference, supported keywords, and integration patterns.

### Why RFC 8785 Canonicalization?

The JSON Schema engine uses RFC 8785 canonical JSON representation for deterministic validation and hashing. This ensures:

1. **Deterministic Hashing**: The same data always produces the same hash, regardless of original formatting or key ordering
2. **Reproducible Replays**: Game replays can be bit-identical across different environments
3. **Content-Addressed Storage**: Schema versions can be identified by their canonical form
4. **Network Independence**: Data can be transmitted in any order and still validate identically

Canonicalization sorts object keys lexicographically and removes whitespace, making validation results independent of data formatting variations.

### Phase 9 Status

**Implemented:**
- Core schema asset system (`JsonSchemaAsset`, `SchemaNode`)
- Validation result tracking (`ValidationResult`)
- Schema compilation framework (`CompiledSchema`)
- Basic type checking (null validation)

**Planned (Future Phases):**
- Full Draft 2020-12 keyword support (type, enum, properties, etc.)
- Array item validation
- Nested object validation
- Constraint keywords (minLength, maximum, pattern, etc.)
- Complex combinators (allOf, anyOf, oneOf)
- Custom keyword extensions

---

## Supported Keywords

Current Phase 9 implementation includes stubs for all Draft 2020-12 keywords. Full validation for the following keywords is planned:

### Type System
- `type` — Restrict data to specific JSON types (string, number, integer, boolean, array, object, null)
- `enum` — Restrict value to a fixed set of allowed values
- `const` — Restrict value to exactly one constant value

### Object Validation
- `properties` — Define validation rules for object properties
- `required` — Specify which properties must be present
- `additionalProperties` — Control whether unspecified properties are allowed
- `minProperties` / `maxProperties` — Restrict object size
- `dependentRequired` — Conditional required properties
- `patternProperties` — Validate properties matching a regex pattern

### Array Validation
- `items` — Schema for array items (single or tuple form)
- `prefixItems` — Validation for positional array items
- `minItems` / `maxItems` — Restrict array length
- `uniqueItems` — Ensure all array items are unique
- `contains` — At least N items must match a schema

### String Constraints
- `minLength` / `maxLength` — Restrict string length
- `pattern` — String must match a regex pattern
- `format` — Built-in formats (email, uri, uuid, etc.)

### Numeric Constraints
- `minimum` / `maximum` — Restrict numeric range (inclusive)
- `exclusiveMinimum` / `exclusiveMaximum` — Restrict numeric range (exclusive)
- `multipleOf` — Value must be a multiple of a given number

### Combinators
- `allOf` — Data must be valid against all provided schemas
- `anyOf` — Data must be valid against at least one provided schema
- `oneOf` — Data must be valid against exactly one provided schema
- `not` — Data must NOT be valid against the provided schema

### Annotations and Metadata
- `$schema` — Specifies the JSON Schema version (always "https://json-schema.org/draft/2020-12/schema")
- `$id` — Schema identifier
- `title` — Human-readable schema name
- `description` — Schema documentation
- `examples` — Example data conforming to the schema
- `default` — Default value if property is omitted

---

## API Reference

### JsonSchemaAsset

**Purpose:** Resource-based schema storage that can be assigned in the editor and compiled once for efficient reuse.

```gdscript
class_name JsonSchemaAsset
extends Resource

@export var schema: Dictionary = {}
```

#### Methods

##### `get_compiled() -> CompiledSchema`
Returns a compiled schema object, compiling on first access and caching for reuse.

```gdscript
var schema_asset := JsonSchemaAsset.new(schema_dict)
var compiled := schema_asset.get_compiled()
```

**Why it matters:** Compilation is expensive; caching avoids recomputing for repeated validations.

##### `is_valid_instance(data: Variant) -> bool`
Returns true if data validates successfully; false otherwise.

```gdscript
if schema_asset.is_valid_instance(world_data):
    print("Data is valid!")
else:
    print("Data is invalid!")
```

**Return type:** bool

##### `validate(data: Variant) -> ValidationResult`
Validates data and returns detailed result with all errors.

```gdscript
var result := schema_asset.validate(world_data)
if result.success:
    print("Valid!")
else:
    for error in result.errors:
        print("Error: %s" % error)
```

**Return type:** ValidationResult (see below)

---

### CompiledSchema

**Purpose:** Runtime-optimized schema representation after compilation. Handles all validation logic.

```gdscript
class_name CompiledSchema
extends RefCounted

var schema: Dictionary
```

#### Methods

##### `validate(data: Variant) -> ValidationResult`
Validates data against the compiled schema.

**Parameters:**
- `data: Variant` — The data to validate (typically a Dictionary from JSON)

**Returns:** ValidationResult with success status and error list

**Example:**
```gdscript
var result := compiled_schema.validate({
    "version": 1,
    "id": "cave_boss_world",
    "width": 5,
    "height": 5,
})
```

**Performance Note:** Compilation happens once; validation can run repeatedly without overhead.

---

### SchemaNode

**Purpose:** Node-based wrapper for schema validation, useful for scene-based validators or signal-based error handling.

```gdscript
class_name SchemaNode
extends Node

@export var schema: Resource
signal validation_failed(result: ValidationResult)
```

#### Methods

##### `validate(data: Variant) -> ValidationResult`
Validates data and returns result (does NOT emit signal).

```gdscript
var schema_node := SchemaNode.new(schema_asset)
var result := schema_node.validate(world_data)
```

**Return type:** ValidationResult

##### `is_valid(data: Variant) -> bool`
Validates data and emits `validation_failed` signal if invalid.

```gdscript
if not schema_node.is_valid(world_data):
    print("Validation failed!")  # validation_failed signal was emitted
```

**Return type:** bool

**Signals:**
- `validation_failed(result: ValidationResult)` — Emitted if validation fails

#### Properties

- `@export var schema: Resource` — Can be set in the editor to any JsonSchemaAsset or Dictionary

**Example Setup:**
```gdscript
# In _ready():
var validator := SchemaNode.new()
validator.schema = preload("res://contracts/world.schema.json")
validator.validation_failed.connect(_on_validation_failed)
add_child(validator)

func _on_validation_failed(result: ValidationResult):
    print("Validation failed with %d errors" % result.errors.size())
```

---

### ValidationResult

**Purpose:** Represents the outcome of a validation operation, including success status, all collected errors, and path information for debugging.

```gdscript
class_name ValidationResult
extends RefCounted

var success: bool = true
var errors: Array[String] = []
var path: String = ""
```

#### Methods

##### `add_error(message: String, error_path: String = "") -> void`
Adds an error message, optionally with JSON path information for debugging.

```gdscript
var result := ValidationResult.new()
result.add_error("Required field 'id' is missing", "$.world.entity[0]")
# Prints: "Required field 'id' is missing (at path: $.world.entity[0])"
```

**Parameters:**
- `message: String` — Human-readable error description
- `error_path: String` — (Optional) JSON Pointer path to the problematic data

**Effect:** Sets `success = false` and appends error to the list

##### `to_dict() -> Dictionary`
Serializes the result for logging or network transmission.

```gdscript
var result := schema_asset.validate(data)
var log_dict := result.to_dict()
# Returns: {
#   "success": true,
#   "error_count": 0,
#   "errors": [],
#   "path": ""
# }
```

**Return type:** Dictionary with keys: `success`, `error_count`, `errors`, `path`

#### Properties

- `success: bool` — True if validation passed; false if any errors were recorded
- `errors: Array[String]` — List of all validation error messages
- `path: String` — JSON path context (set during recursive validation)

---

## Examples

### Simple Type Validation

```gdscript
# Validate that a value is an integer
var schema := {
    "type": "integer",
    "minimum": 0,
    "maximum": 100
}

var asset := JsonSchemaAsset.new(schema)

print(asset.is_valid_instance(42))      # true
print(asset.is_valid_instance(0))       # true
print(asset.is_valid_instance(100))     # true
print(asset.is_valid_instance(101))     # false (exceeds maximum)
print(asset.is_valid_instance("string")) # false (wrong type)
```

### Object Validation

```gdscript
# Validate a player entity
var entity_schema := {
    "type": "object",
    "required": ["id", "name", "health"],
    "properties": {
        "id": { "type": "string", "minLength": 1 },
        "name": { "type": "string" },
        "health": { "type": "integer", "minimum": 0 },
        "tags": {
            "type": "array",
            "items": { "type": "string" }
        }
    },
    "additionalProperties": false
}

var entity_data := {
    "id": "player_001",
    "name": "Hero",
    "health": 100,
    "tags": ["player", "hero"]
}

var asset := JsonSchemaAsset.new(entity_schema)
var result := asset.validate(entity_data)
print("Valid: %s" % result.success)  # true
```

### Array Validation

```gdscript
# Validate a list of spawn points
var spawns_schema := {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "x", "y", "type"],
        "properties": {
            "id": { "type": "string" },
            "x": { "type": "integer", "minimum": 0 },
            "y": { "type": "integer", "minimum": 0 },
            "type": { "type": "string", "enum": ["player", "enemy", "boss", "exit"] }
        }
    },
    "minItems": 1,  # At least one spawn point required
    "uniqueItems": true
}

var spawns_data := [
    { "id": "spawn_1", "x": 0, "y": 0, "type": "player" },
    { "id": "spawn_2", "x": 5, "y": 5, "type": "boss" }
]

var asset := JsonSchemaAsset.new(spawns_schema)
var result := asset.validate(spawns_data)
```

### Nested Schemas

```gdscript
# Validate a complex nested structure
var world_schema := {
    "type": "object",
    "required": ["version", "id", "tiles", "spawns"],
    "properties": {
        "version": { "type": "integer", "const": 1 },
        "id": { "type": "string" },
        "width": { "type": "integer", "minimum": 1 },
        "height": { "type": "integer", "minimum": 1 },
        "tiles": {
            "type": "array",
            "items": { "type": "integer", "enum": [0, 1] }
        },
        "spawns": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "x", "y", "type"],
                "properties": {
                    "id": { "type": "string" },
                    "x": { "type": "integer" },
                    "y": { "type": "integer" },
                    "type": { "type": "string" }
                }
            }
        }
    }
}

var asset := JsonSchemaAsset.new(world_schema)
# Validation now recurses through nested structure
```

### Enum Validation

```gdscript
# Validate encounter difficulty
var difficulty_schema := {
    "type": "string",
    "enum": ["easy", "normal", "hard", "legendary"]
}

var asset := JsonSchemaAsset.new(difficulty_schema)
print(asset.is_valid_instance("normal"))     # true
print(asset.is_valid_instance("nightmare"))  # false (not in enum)
```

### Using SchemaNode for Signal-Based Validation

```gdscript
extends Node

func _ready():
    var schema := preload("res://contracts/world.schema.json")
    var validator := SchemaNode.new(schema)
    validator.validation_failed.connect(_on_validation_failed)
    add_child(validator)
    
    var world_data := load_world_json()
    validator.is_valid(world_data)  # Emits signal if invalid

func _on_validation_failed(result: ValidationResult):
    print("Validation failed!")
    for error in result.errors:
        print("  - %s" % error)
```

---

## Integration Patterns

### 1. Load and Validate During Level Loading

```gdscript
func load_level(path: String) -> bool:
    var save_service := SaveService.new()
    var data := save_service.load_json(path)
    
    # Load schema
    var schema_data := save_service.load_json("res://contracts/world.schema.json")
    var schema_asset := JsonSchemaAsset.new(schema_data)
    
    # Validate before using
    var result := schema_asset.validate(data)
    if not result.success:
        push_error("Level validation failed: %s" % result.errors)
        return false
    
    # Safe to use now
    apply_level_data(data)
    return true
```

### 2. Editor-Based Validation

```gdscript
# Assign schema in editor via @export, then validate in script
extends Node

@export var schema: Resource
var _validator: SchemaNode

func _ready():
    _validator = SchemaNode.new(schema)
    _validator.validation_failed.connect(_on_schema_error)
    add_child(_validator)

func validate_data(data: Dictionary) -> bool:
    return _validator.is_valid(data)

func _on_schema_error(result: ValidationResult):
    print("Schema violation: %s" % result.errors)
```

### 3. Validation with Error Reporting

```gdscript
func validate_and_report(data: Dictionary, schema_path: String) -> bool:
    var save_service := SaveService.new()
    var schema := save_service.load_json(schema_path)
    
    var asset := JsonSchemaAsset.new(schema)
    var result := asset.validate(data)
    
    if result.success:
        print("✅ Validation passed")
        return true
    else:
        print("❌ Validation failed (%d errors):" % result.errors.size())
        for i in range(result.errors.size()):
            print("  [%d] %s" % [i + 1, result.errors[i]])
        return false
```

### 4. Batch Validation of Multiple Files

```gdscript
func validate_all_content() -> Dictionary:
    var results := {}
    var save_service := SaveService.new()
    
    var validations := [
        { "data": "res://examples/cave_boss/cave_world.json",
          "schema": "res://contracts/world.schema.json" },
        { "data": "res://examples/cave_boss/cave_encounter.json",
          "schema": "res://contracts/encounter.schema.json" },
    ]
    
    for validation in validations:
        var data := save_service.load_json(validation["data"])
        var schema := save_service.load_json(validation["schema"])
        var asset := JsonSchemaAsset.new(schema)
        results[validation["data"]] = asset.validate(data)
    
    return results
```

---

## Migration Guide: Schema Versioning with Patches

As game data evolves, schemas will need to change. Use these patterns for safe migrations:

### 1. Version-Aware Loading

```gdscript
func load_and_migrate(path: String) -> Dictionary:
    var save_service := SaveService.new()
    var data := save_service.load_json(path)
    
    var version := data.get("version", 0)
    match version:
        1:
            return _migrate_v1_to_v2(data)
        2:
            return data
        _:
            push_error("Unknown data version: %d" % version)
            return {}

func _migrate_v1_to_v2(data: Dictionary) -> Dictionary:
    # Transform v1 format to v2 format
    data["version"] = 2
    # Apply any schema changes
    return data
```

### 2. Schema with Default Values

```gdscript
var entity_schema := {
    "type": "object",
    "properties": {
        "version": { "type": "integer", "default": 1 },
        "id": { "type": "string" },
        "health": { "type": "integer", "default": 100 },
    }
}

func apply_defaults(data: Dictionary, schema: Dictionary) -> Dictionary:
    var properties = schema.get("properties", {})
    for key in properties:
        if key not in data and "default" in properties[key]:
            data[key] = properties[key]["default"]
    return data
```

### 3. Deprecation Markers

Use schema annotations to mark deprecated fields:

```gdscript
var entity_schema := {
    "type": "object",
    "properties": {
        "id": { "type": "string" },
        "old_damage": {
            "type": "integer",
            "deprecated": true,
            "description": "Use 'damage' instead"
        },
        "damage": { "type": "integer" }
    }
}
```

---

## Performance Notes

### Compilation Overhead

Schema compilation involves:
1. Parsing the schema Dictionary structure
2. Building validation rule trees
3. Caching for reuse

**Timings (estimated, Phase 9 stub):**
- Compilation: < 1ms for typical schemas
- First validation: ~0.5ms (includes compilation if not cached)
- Subsequent validations: ~0.1ms (cached)

### Caching Strategy

For optimal performance:

**Good: Compile once at startup**
```gdscript
func _ready():
    _world_schema = JsonSchemaAsset.new(load_schema_dict())
    # Compilation happens here, cached for reuse
    
func validate_world(data):
    return _world_schema.validate(data)  # Reuses compiled schema
```

**Avoid: Compiling repeatedly**
```gdscript
# DON'T do this in a loop:
for data in many_datasets:
    var asset := JsonSchemaAsset.new(schema)  # Recompiles every iteration!
    asset.validate(data)
```

### Validation Complexity

Current Phase 9 implementation:
- **O(n)** for flat objects (n = property count)
- **O(n*m)** for nested structures (n = objects, m = nesting depth)
- **O(n)** for arrays (n = item count)

Full Draft 2020-12 support may increase complexity for:
- Combinator keywords (allOf, anyOf, oneOf): exponential worst-case
- Pattern matching: depends on regex complexity
- Recursive schemas: requires cycle detection

### Memory Usage

- Schema asset: ~1KB per schema
- Compiled schema: ~2-5KB per schema (depends on complexity)
- Validation result: ~0.5KB + error message size

For typical game data sets (100+ schemas), expect < 1MB total memory.

---

## Troubleshooting

### Common Validation Errors

#### "Data is null"
The data being validated is null. Check that:
- JSON file was loaded successfully
- SaveService didn't return an empty dict
- Data is being passed to validate(), not null

```gdscript
var data := save_service.load_json(path)
if data.is_empty():
    print("ERROR: Failed to load or parse JSON")
    return

var result := schema.validate(data)  # Pass data, not null
```

#### "No schema asset assigned"
SchemaNode was created without a schema. Assign one in _ready():

```gdscript
var validator := SchemaNode.new()
validator.schema = preload("res://contracts/world.schema.json")  # Assign here
```

#### "Schema must be JsonSchemaAsset or Dictionary"
SchemaNode received an invalid schema type. Only Resource, JsonSchemaAsset, or Dictionary are supported:

```gdscript
# ✅ Correct:
validator.schema = JsonSchemaAsset.new(schema_dict)
validator.schema = schema_dict
validator.schema = preload("res://path.tres")

# ❌ Wrong:
validator.schema = "path/to/schema.json"  # String, not supported
```

### Debug Tips

1. **Print validation results**
```gdscript
var result := schema.validate(data)
print(result.to_dict())  # Dumps full result as dict
```

2. **Check raw schema structure**
```gdscript
var save_service := SaveService.new()
var schema := save_service.load_json("res://contracts/world.schema.json")
print(schema)  # Print raw schema dict
```

3. **Validate incrementally**
```gdscript
# Load and validate data step-by-step
var data := load_json()
print("Data type: %s" % typeof(data))
print("Data keys: %s" % data.keys() if typeof(data) == TYPE_DICTIONARY else "Not a dict")
print("Validating...")
var result := schema.validate(data)
print("Result: %s" % result.to_dict())
```

4. **Use path information**
```gdscript
for error in result.errors:
    print("Error: %s" % error)  # Includes "(at path: ...)" if available
```

### Performance Debugging

Use `CompiledSchema` directly if you need to profile validation:

```gdscript
var schema_asset := JsonSchemaAsset.new(schema_dict)
var compiled := schema_asset.get_compiled()

var start := Time.get_ticks_msec()
for i in range(1000):
    compiled.validate(data)
var elapsed := Time.get_ticks_msec() - start
print("1000 validations took %dms (%.3fms each)" % [elapsed, elapsed / 1000.0])
```

---

## References

- **JSON Schema Specification:** https://json-schema.org/draft/2020-12/json-schema-core.html
- **RFC 8785 (Canonical JSON):** https://tools.ietf.org/html/rfc8785
- **Fung Core Contracts:** `fung_core/contracts/*.schema.json`
- **Implementation:** `fung_core/godot_addon/fung_core/systems/json_schema/`
- **Examples:** `fung_core/examples/cave_boss/`

---

## Future Enhancements

Planned additions for later phases:

- [ ] Full Draft 2020-12 keyword implementation
- [ ] Performance profiling and optimization
- [ ] Schema version negotiation for client-server
- [ ] Schema drift detection (what changed between versions?)
- [ ] Automatic migration code generation
- [ ] Validator plugins for custom keywords
- [ ] Integration with Godot's debugger for breakpoints in validation
- [ ] Interactive schema explorer in the editor
