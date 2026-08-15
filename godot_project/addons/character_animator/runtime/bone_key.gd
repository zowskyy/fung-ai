class_name BoneKey
extends Resource
## A keyframe for one bone inside a BoneTrack.

@export var time: float = 0.0
@export var position: Vector2 = Vector2.ZERO
@export var rotation: float = 0.0
@export var scale: Vector2 = Vector2.ONE


func duplicate_key() -> BoneKey:
	var copy := BoneKey.new()
	copy.time = time
	copy.position = position
	copy.rotation = rotation
	copy.scale = scale
	return copy
