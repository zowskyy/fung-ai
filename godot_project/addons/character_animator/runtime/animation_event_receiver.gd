class_name AnimationEventReceiver
extends Node
## Receives method-call track events from AnimationPlayer clips and re-emits
## them as a single, game-facing signal.
##
## Animation method tracks should call emit_event("footstep", "left") rather
## than arbitrary gameplay methods, so VFX/SFX/hitbox systems subscribe once.

signal animation_event(event_name: StringName, payload: Variant)

const EVENT_VOCABULARY: PackedStringArray = [
	"footstep",
	"spawn_dust",
	"hitbox_open",
	"hitbox_close",
	"combo_open",
	"land",
	"jump",
]


func emit_event(event_name: StringName, payload: Variant = null) -> void:
	animation_event.emit(event_name, payload)


func has_event(event_name: StringName) -> bool:
	return EVENT_VOCABULARY.has(String(event_name))
