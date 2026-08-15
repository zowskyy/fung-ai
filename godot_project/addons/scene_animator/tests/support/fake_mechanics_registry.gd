class_name FakeMechanicsRegistry
extends SceneMechanicsRegistry

## Recording mechanics registry. Mirrors production dispatch (invokes the
## registered effect callable and emits effects_requested via the base), while
## also recording every play_effect call with a shallow-copied context so
## adapter identity survives for assertions.

var calls: Array[Dictionary] = []

## Effect IDs that should be treated as unregistered (presence gate only).
## When set, has_effect() reports false so the dialogue runner skips dispatch
## for that ID. This models a missing/unregistered effect, not a dispatch
## failure of an existing effect, which Phase 1 does not yet exercise.
var unregistered_effect_ids: Dictionary[StringName, bool] = {}


func has_effect(effect_id: StringName) -> bool:
	if unregistered_effect_ids.has(effect_id):
		return false
	return super.has_effect(effect_id)


func play_effect(effect_id: StringName, payload: Dictionary = {}) -> void:
	calls.append({
		"effect_id": effect_id,
		"context": payload.duplicate(false),
	})
	super.play_effect(effect_id, payload)
