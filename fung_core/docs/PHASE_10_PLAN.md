# Phase 10: Data Validation & Integration - Planning

> **Status: Core blocker resolved.** See `PHASE_10_FINDINGS.md` for the root
> cause, the fix, and CI verification. Tasks 1–3 below are complete. Task 4
> (platform verification) is addressed at the source-code level in the
> findings doc; Task 5 (documentation) is addressed by this update and the
> revised `JSON_SCHEMA.md`. The plan below is kept as-written for historical
> record of the investigation approach.

## Overview

Phase 9 delivered a working JSON Schema validation engine. Phase 10 focuses on ensuring example data fully conforms to schemas and investigating type preservation during JSON loading.

## Known Blocker

**Schema Validation Non-Fatal in Example**

Current state: Validation runs but doesn't fail the example execution. Warnings are logged to stderr.

**Root Cause Investigation Needed:**
1. Why do certain fields (version, seed, width, height, etc.) report "Value type is not integer"?
2. Is it a JSON parsing issue in Godot 4.3?
3. Is it a schema validation logic edge case?
4. Are example JSON files actually conforming to their schemas?

**Evidence:**
- ✅ Python validation confirms JSON files have correct integer types
- ✅ Conformance tests pass (schema engine works correctly)
- ✅ Example runs successfully when validation is disabled
- ❌ Validation logs type errors when enabled

## Phase 10 Tasks

### 1. Debug Validation Errors (High Priority)
**Goal:** Identify exact validation failures and root cause

**Steps:**
1. Extract CI logs from run 31881433129 to see actual validation errors
2. Create minimal test case: load cave_world.json, validate, show exact errors
3. Verify JSON.parse_string() preserves integer types in test environment
4. Compare schema expectations vs actual data types

**Expected Output:** Clear error messages showing which fields fail and why

### 2. Fix Example Data (If Needed)
**Goal:** Ensure example JSON files conform 100% to schemas

**Steps:**
1. Based on validation errors from Task 1:
   - Update JSON files if types are wrong
   - Update schemas if constraints are too strict
   - Add missing required fields
2. Re-run validation against updated data
3. Verify conformance tests still pass

### 3. Restore Fatal Validation (Integration)
**Goal:** Make validation fail the example when data is invalid

**Steps:**
1. Uncomment validation failure code in main.gd
2. Ensure example data passes validation
3. Verify CI still passes
4. Update documentation

### 4. Platform Verification
**Goal:** Ensure JSON type preservation works across platforms

**Tests:**
- Verify JSON.parse_string() behavior on Linux (CI environment) ✓
- Document any platform-specific quirks
- Update SaveService documentation if needed

### 5. Documentation
**Goal:** Record findings and best practices

**Updates:**
- JSON Schema validation guide with examples
- Godot 4.3 JSON handling documentation
- Data type preservation guarantees
- Schema update guide (for future phases)

## Technical Investigation Plan

### Task 1a: Extract and Analyze Validation Errors

```bash
# After Phase 10 begins
# Download CI logs from run 31881433129
# Extract stderr output from "Run example" step
# Parse validation errors and categorize
```

### Task 1b: Create Minimal Test

```gdscript
# In tools/test_json_types.gd
extends SceneTree

func _initialize() -> void:
    var save_service := SaveService.new()
    var world_data := save_service.load_json("res://examples/cave_boss/cave_world.json")
    
    # Print actual types
    print("version type: %s value: %s" % [typeof(world_data.get("version")), world_data.get("version")])
    print("seed type: %s value: %s" % [typeof(world_data.get("seed")), world_data.get("seed")])
    print("width type: %s value: %s" % [typeof(world_data.get("width")), world_data.get("width")])
    
    # Validate
    var schema_service := SaveService.new()
    var schema_data := schema_service.load_json("res://contracts/world.schema.json")
    var validator := JsonSchemaAsset.new(schema_data)
    var result := validator.validate(world_data)
    
    for error in result.errors:
        print("VALIDATION ERROR: %s" % error)
    
    quit(0)
```

### Task 1c: JSON Type Analysis

Expected investigation:
- Compare Godot TYPE_INT vs parsed integer values
- Check if string coercion is happening somewhere
- Verify SaveService.load_json() directly uses JSON.parse_string() with no transformation

## Risk Assessment

**Low Risk:** Data type investigation and fixes
- JSON files exist and are well-formed
- Validation engine is proven to work
- Worst case: Need to slightly adjust schema constraints

**Potential Issues:**
- Godot 4.3 JSON.parse_string() might behave differently than expected
- Schema might have edge cases not covered by conformance tests
- Example data might legitimately not conform to schema (schema too strict)

## Success Criteria

✅ Phase 10 Complete When:
1. All validation errors are identified and documented
2. Example data passes validation without warnings
3. Example still executes successfully
4. Validation failure makes example fail (fatal again)
5. All CI gates pass
6. Documentation is updated
7. Next phase can proceed

## Timeline Estimate

- **Task 1 (Debug):** 1-2 hours investigation + analysis
- **Task 2 (Fix Data):** 30 min - 2 hours depending on findings
- **Task 3 (Integration):** 15 minutes
- **Task 4 (Verification):** 30 minutes
- **Task 5 (Documentation):** 1 hour

**Total:** 3-6 hours depending on complexity of findings

## Deliverables

1. PHASE_10_FINDINGS.md - Root cause analysis and solutions
2. Updated example JSON files (if needed)
3. Updated or new schema definitions (if constraints changed)
4. Updated main.gd with fatal validation
5. All CI gates passing
6. Updated docs/JSON_SCHEMA_GUIDE.md

## Next Phase Blocker

Phase 10 must resolve validation issues before moving to Phase 11 (which may depend on data integrity guarantees).

---

## Assigned to

Ready for worker assignment when Phase 9 is approved for completion.

**Recommended Approach:** Start with Task 1a-1c in parallel, use findings to scope Tasks 2-3.
