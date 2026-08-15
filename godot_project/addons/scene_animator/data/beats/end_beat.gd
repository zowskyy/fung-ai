@tool
class_name EndBeat
extends SceneBeat

## Terminates the sequence. Emits `scene_finished` via the director.

@export var completion_signal: StringName = &"scene_finished"


func beat_type() -> StringName:
	return &"end"
