@tool
class_name DialogueBeat
extends SceneBeat

## Triggers a registered dialogue line. Completion is driven by the dialogue
## adapter's `dialogue_finished` event.

@export_category("Dialogue")
@export var dialogue_id: StringName
@export var speaker_actor_id: StringName
@export var target_actor_id: StringName
@export var timeout_seconds := 20.0


func beat_type() -> StringName:
	return &"dialogue"
