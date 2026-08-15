# Phase 10 Findings: Integer Validation Root Cause

## Status: ✅ RESOLVED

**Fix commits:** `bc62b95` (root cause fix), `877930d` (restore fatal validation)
**Verified via:** CI run on PR #2 — `godot-checks` job, `Run example` step

## Summary

The cave_boss example's schema validation logged `"Value type is not integer"`
for fields (`version`, `seed`, `width`, `height`, tile values, spawn
coordinates) that Python's `jsonschema` library — and manual inspection of
the raw JSON — confirmed were correctly-typed integers. Phase 9 shipped with
this non-fatal, logging warnings but not failing the example, pending
investigation.

## Root Cause

`fung_core/godot_addon/fung_core/systems/json_schema/compiled_schema.gd`
implemented the `"integer"` JSON Schema type check as:

```gdscript
"integer":
    return data_type == TYPE_INT
```

This is correct only if the data actually carries Godot's `TYPE_INT` tag.
It doesn't, because of how Godot's JSON parser works:

- JSON's grammar has exactly one numeric literal form (`number`) — there is
  no separate integer token, unlike GDScript's `int`/`float` split.
- Godot's `JSON.parse_string()` (engine-level C++, `core/io/json.cpp`)
  deserializes every JSON `number` into a GDScript `float` (`TYPE_FLOAT`),
  regardless of whether the literal in the source text had a decimal point.
- So `"version": 1` in `cave_world.json` comes back from
  `JSON.parse_string()` as `1.0` (`TYPE_FLOAT`), not `1` (`TYPE_INT`).

The strict `TYPE_INT` check therefore rejected every JSON-sourced integer
field, unconditionally — this wasn't a data problem or an edge case, it
would fail on any valid input.

### Why the conformance tests didn't catch it

The 16 conformance tests in `tools/conformance_runner.gd` constructed their
test fixtures as GDScript literal dictionaries (e.g. `{"version": 1}`)
directly in source, not via `JSON.parse_string()`. GDScript integer literals
without a decimal point produce genuine `TYPE_INT` values, so those tests
passed while real file-sourced data failed. This is the gap Phase 10 was
opened to close.

## Fix

`_validate_single_type()`'s `"integer"` case now accepts a `TYPE_FLOAT`
value if it has a zero fractional part:

```gdscript
"integer":
    if data_type == TYPE_INT:
        return true
    if data_type == TYPE_FLOAT:
        return float(data) == floor(float(data))
    return false
```

This isn't a workaround — it's the spec-correct behavior. JSON Schema
Draft 2020-12 defines `"integer"` as "a JSON number without a fraction or
exponent part" (i.e., a number with a zero fractional part), not as
"whatever the host language's native integer tag is." `5.0` and `5` are
both valid instances of `{"type": "integer"}` per spec; Godot's chosen
internal representation for JSON-sourced numbers shouldn't change that.

## Verification

Confirmed via live CI logs (not assumed from the diff):

```
Validating world data against schema...
✅ VALIDATION PASSED
The cave_world.json data conforms to world.schema.json
[main] Schema validation passed
...
run_example: SUCCESS - Vertical slice completed successfully
...
replay_check: PASS - seed=42 final_hash=b107699913e1d61772d6b8efc0a258dbfab8178f9a9fdec517e6c66e19977613
```

`godot-checks` passed on both fix commits. Validation was then restored to
fatal (`main.gd` now calls `notify_finished(false, ...)` and returns on a
failed validation result instead of logging and continuing), and the
example still completes successfully — confirming the fix, not just the
absence of a crash.

## Other Phase 10 Investigation Questions — Answered

**Is it a JSON parsing issue in Godot 4.3?**
Yes, specifically: `JSON.parse_string()` collapses the JSON number type into
GDScript `float` unconditionally. This isn't a bug in Godot — it's a
documented consequence of JSON not having a distinct integer grammar — but
it's a real gotcha for anyone writing a JSON Schema validator against
Godot-parsed data, since the "obvious" implementation (`typeof(x) ==
TYPE_INT`) silently rejects all valid input.

**Is it a schema validation logic edge case?**
No — it was unconditional, not an edge case. Any integer-typed field in any
schema, validated against any JSON-file-sourced data, would have failed.

**Are example JSON files actually conforming to their schemas?**
Yes. No JSON file or schema needed to change. Confirmed by both the earlier
Python `jsonschema` validation (Phase 9) and now the fixed GDScript engine
agreeing.

## Platform Scope

`JSON.parse_string()` is implemented in Godot's portable core (`core/io/json.cpp`),
with no OS-conditional branches around numeric parsing. The float-collapse
behavior is therefore expected to be identical on every platform Godot
targets (Linux, Windows, macOS, mobile, web) — this is a property of the
engine's JSON grammar handling, not of the host OS. This has only been
observed directly in the Linux CI runner; it has not been empirically
re-verified on other platforms in this phase, since Phase 10 has no access
to non-Linux CI runners. If a platform-specific discrepancy ever surfaces,
start by checking `core/io/json.cpp` for the specific engine build in use.

## What Changed vs. What Didn't

| Item | Changed? |
|---|---|
| `compiled_schema.gd` integer type check | ✅ Fixed |
| `main.gd` validation fatality | ✅ Restored to fatal |
| Example JSON files (`cave_world.json`, etc.) | No change needed |
| Schema files (`world.schema.json`, etc.) | No change needed |
| Conformance test fixtures | No change (gap noted above, not closed — see Follow-ups) |

## Follow-ups (Not Blocking)

- The conformance suite's use of GDScript literals instead of
  `JSON.parse_string()`-sourced fixtures means it can't by itself catch a
  float/int mismatch like this one again. Adding at least one conformance
  case that round-trips through `JSON.stringify()` → `JSON.parse_string()`
  before validating would close that gap.
- The same `TYPE_INT`-only assumption is worth double-checking anywhere
  else in the codebase that branches on `typeof()` for JSON-sourced data
  (none found elsewhere in `json_schema/` as of this writing — `"number"`
  already accepted both `TYPE_INT` and `TYPE_FLOAT`).
