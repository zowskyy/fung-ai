# Worker Code Quality and Validation System

## Critical Mandate: Phase-Gate Discipline

**BEFORE MARKING ANY WORK COMPLETE:** Verify the CI gate passes. Do not rely on local checks or assumptions. This is non-negotiable.

---

## Godot 4.3 Specific Requirements

### @export Annotation MUST Have Initialization
```gdscript
# WRONG - Parse error in Godot 4.3
@export var schema: Variant

# CORRECT - Always initialize @export variables
@export var schema: Variant = null
@export var count: int = 0
@export var list: Array = []
```

This is non-negotiable. Every @export variable needs explicit initialization or CI will fail.

### Type Changes Require Full Review
When changing a variable's type (Resource → Variant, etc.):
1. Add explicit @export initialization immediately
2. Review ALL usages of that variable
3. Verify type guards (`is Dictionary`, `is CustomClass`) still work
4. Check function signatures that accept/return that type
5. Only commit after full file review

### Function Naming
Avoid names that conflict with Godot built-ins:
- ❌ `func log(...)` - conflicts with `log(x)` (math function)
- ✅ `func write_log(...)` or `func print_log(...)`

Check Godot API docs before naming functions.

## GDScript Syntax Safeguards

### ❌ FORBIDDEN Patterns (Will cause CI failure)

**Python try/except in GDScript:**
```gdscript
# WRONG - Python syntax, not valid GDScript
try:
    regex.compile(value)
except:
    pass
```

**Always use GDScript if/else:**
```gdscript
# CORRECT - GDScript pattern
if regex.compile(value) != OK:
    push_error("Failed to compile regex")
else:
    schema["__compiled_pattern"] = regex
```

### Constructor Parameter Validation

**Verify required parameters before instantiation:**
```gdscript
# WRONG - CompiledSchema._init() requires schema: Dictionary
var compiled := CompiledSchema.new()

# CORRECT - Pass required parameter
var compiled := CompiledSchema.new({})
```

**Check function signatures:**
```gdscript
# Before writing: CompiledSchema._init(schema: Dictionary) -> void
# This requires a Dictionary argument in all calls
```

### Code Review Before Commit

**MANDATORY: Read entire file before committing**

When editing a file:
1. Make your changes
2. Read the ENTIRE file (`Read` tool from line 1 to end)
3. Scan for:
   - Python-style syntax (try/except, list comprehensions, f-strings)
   - Unreachable code (return statements in match blocks, dead code)
   - Missing class_name declarations
   - Constructor calls with wrong argument count
   - Invalid property access (accessing private `_var` as public)
   - Incomplete error handling blocks
4. Only then commit

**Pattern to follow:**
```
1. Edit the file
2. Read entire file top to bottom
3. Verify no Python patterns exist
4. Check all constructor calls have required arguments
5. Verify all class_name declarations are present
6. Scan for unreachable code
7. THEN commit with message explaining what you reviewed
```

---

## Pre-Commit Validation Checklist

**For EVERY commit, verify:**

- [ ] Entire file read and scanned (not just changed lines)
- [ ] No Python syntax (try/except, except/finally, raise, assert)
- [ ] No unreachable code (extra returns, dead branches)
- [ ] All class_name declarations present
- [ ] All constructor calls have required parameters
- [ ] No private property access (accessing `_private` as public)
- [ ] String formatting uses `%` not f-strings
- [ ] Error handling uses if/else not try/except
- [ ] Match statements don't have code after final return

**Commit message must reference the review:**
```
Fix X in file.gd

- Reviewed entire file (N lines)
- Verified no Python syntax patterns
- Checked constructor calls have required args
- Scanned for unreachable code at line X

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

---

## CI Gate Verification (Phase-Gate Discipline)

**After pushing, ALWAYS verify CI passes:**

1. Push changes: `git push -u origin branch-name`
2. Check workflow status: `mcp__github__actions_list` → `list_workflow_runs`
3. Wait for completion (do not assume success)
4. Get final result: `mcp__github__actions_get` → `get_workflow_run`
5. Verify `conclusion` is `success` (not `failure`, not `null`)
6. If failed: read error logs, fix root cause, repeat from step 1
7. Only mark task complete when CI conclusion is `success`

**Valid conclusions:**
- ✅ `"success"` — Gate passed, proceed to next phase
- ❌ `"failure"` — Gate failed, fix and rerun
- ⏳ `null` — Still in_progress, wait and check again

---

## Godot/GDScript-Specific Rules

### Type Annotations Always

```gdscript
# WRONG
var value = something

# CORRECT
var value: String = something
var result := compiled.validate(data)  # Type inferred
```

### Null Safety

```gdscript
# WRONG - Crashes if null
return data.validate()

# CORRECT - Defensive check
if data == null:
    return null
return data.validate()
```

### Signal Emission

```gdscript
# CORRECT - Always use .emit()
validation_failed.emit(result)

# NOT .send_message() or .call()
```

### Resource vs RefCounted

- `extends Resource` for persistent assets (schemas, configs)
- `extends RefCounted` for transient objects (results, jobs)
- Never both

---

## File Structure Validation

**Every GDScript file must have:**
1. Class name declaration (if public API)
   ```gdscript
   class_name MyClass
   extends Node
   ```
2. Docstring explaining purpose
3. Clear public/private separation
4. _init() signature documented

**Example template:**
```gdscript
class_name SchemaValidator
extends RefCounted

## Validates JSON data against schema.

func _init(schema: Dictionary) -> void:
    # initialization

func validate(data: Variant) -> ValidationResult:
    # main method
```

---

## Common Errors and Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Parse Error: Could not resolve class 'X'` | Syntax error earlier in file | Read entire file, find Python syntax or unreachable code |
| `Too few arguments for 'new()' call` | Missing required parameter | Check `_init()` signature, pass all required args |
| `Identifier 'X' not declared` | Missing `class_name` or import | Add `class_name X` at top of file |
| `Invalid access to private member '_X'` | Accessing private property | Use public property or getter method |
| `Unexpected 'except' keyword` | Python syntax in GDScript | Replace try/except with if/else |

---

## Worker Completion Criteria

A task is ONLY complete when:

1. ✅ Code written and reviewed
2. ✅ Entire file scanned for errors
3. ✅ Committed with verification checklist in message
4. ✅ Pushed to correct branch
5. ✅ **CI workflow run to completion**
6. ✅ **Workflow conclusion verified as `success`**
7. ✅ Phase gate status reported to user

**No step can be skipped. No assumptions about CI status.**

---

## Prevention Summary

**What broke Phase 9:**
- Generated code without validation
- Python patterns in GDScript
- Unreachable code not caught by linter
- Constructor parameter mismatches
- Missing class declarations

**What prevents it now:**
- Mandatory file review before every commit
- Explicit syntax safeguards
- Mandatory CI gate verification
- Detailed commit messages explaining review
- Clear completion criteria requiring real CI results

**Worker responsibility:** Follow this checklist. Period. No shortcuts.
