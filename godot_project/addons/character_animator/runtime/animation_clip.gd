class_name AnimationClip
extends Resource
## A named clip of sprite-sheet frame regions.
##
## Frames are Rect2 regions in texture-pixel coordinates into the texture of
## the CharacterAnimator (or generated Animation) that plays the clip. fps
## drives playback speed and loop controls whether the clip wraps or stops on
## the last frame.

@export var name: StringName = &""
@export var frames: Array[Rect2] = []
@export var fps: float = 10.0
@export var loop: bool = true
@export var flip_h: bool = false
@export var flip_v: bool = false


func frame_count() -> int:
	return frames.size()


func duration() -> float:
	if frames.is_empty() or fps <= 0.0:
		return 0.0
	return float(frames.size()) / fps


func add_frame(region: Rect2) -> void:
	frames.append(region)


func insert_frame(index: int, region: Rect2) -> void:
	frames.insert(clampi(index, 0, frames.size()), region)


func remove_frame(index: int) -> void:
	if index >= 0 and index < frames.size():
		frames.remove_at(index)


func move_frame(from_index: int, to_index: int) -> void:
	if frames.size() < 2:
		return
	from_index = clampi(from_index, 0, frames.size() - 1)
	to_index = clampi(to_index, 0, frames.size() - 1)
	if from_index == to_index:
		return
	var region := frames[from_index]
	frames.remove_at(from_index)
	frames.insert(to_index, region)


func frame_rect(index: int) -> Rect2:
	if frames.is_empty():
		return Rect2()
	return frames[clampi(index, 0, frames.size() - 1)]
