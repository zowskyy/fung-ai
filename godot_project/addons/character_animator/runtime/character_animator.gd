class_name CharacterAnimator
extends Sprite2D
## Frame-clip sprite animator (the "simple" playback path).
##
## Holds a dictionary of AnimationClip resources keyed by name and advances
## its own Sprite2D region through the current clip's frames in _process.
## Flipping is driven per clip with global overrides available.
##
## The same clips can instead be converted into an AnimationPlayer +
## AnimationTree by AnimationGraphBuilder so the node is purely a clip source;
## set auto_play to false in that case.
##
## Signals:
##   animation_started(animation)   fired when play() begins a clip
##   animation_finished(animation)  fired when a non-looping clip ends
##   clip_frame_changed(index)      fired whenever the shown frame changes

signal animation_started(animation: StringName)
signal animation_finished(animation: StringName)
signal clip_frame_changed(index: int)

@export var clips: Dictionary = {}
@export var initial_animation: StringName = &""
@export var auto_play: bool = true
@export var speed_scale: float = 1.0
@export var global_flip_h: bool = false
@export var global_flip_v: bool = false

var current_animation: StringName = &""
var frame_index: int = 0
var is_playing: bool = false
var paused: bool = false

var _frame_time: float = 0.0
var _direction: int = 1


func _ready() -> void:
	region_enabled = true
	if auto_play and initial_animation != &"":
		play(initial_animation)


func has_animation(animation_name: StringName) -> bool:
	return clips.has(animation_name)


func get_clip(animation_name: StringName) -> AnimationClip:
	return clips.get(animation_name) as AnimationClip


func animation_names() -> PackedStringArray:
	var names := PackedStringArray()
	for name in clips:
		names.append(name)
	return names


func play(animation_name: StringName, from_begin: bool = true) -> void:
	var clip := get_clip(animation_name)
	if clip == null:
		push_warning("CharacterAnimator.play: no clip named '%s'." % animation_name)
		return
	current_animation = animation_name
	is_playing = true
	paused = false
	_direction = -1 if speed_scale < 0.0 else 1
	if from_begin:
		frame_index = 0 if _direction >= 0 else clip.frame_count() - 1
		_frame_time = 0.0
	_apply_frame()
	animation_started.emit(animation_name)


func stop() -> void:
	is_playing = false
	paused = false
	_frame_time = 0.0


func pause() -> void:
	paused = true


func resume() -> void:
	if is_playing:
		paused = false


func restart() -> void:
	if current_animation != &"":
		play(current_animation, true)


func _process(delta: float) -> void:
	advance(delta)


## Advances playback by delta seconds. Extracted from _process so tests and
## deterministic tools can step the animator without waiting for frames.
func advance(delta: float) -> void:
	if not is_playing or paused:
		return
	var clip := get_clip(current_animation)
	if clip == null or clip.frames.is_empty():
		return
	_frame_time += delta * absf(speed_scale) * clip.fps
	var steps := int(_frame_time)
	if steps > 0:
		_frame_time -= float(steps)
		_advance(steps * _direction, clip)


func _advance(steps: int, clip: AnimationClip) -> void:
	var count := clip.frame_count()
	if count <= 0:
		return
	frame_index += steps
	if frame_index >= count:
		if clip.loop:
			frame_index = frame_index % count
		else:
			frame_index = count - 1
			is_playing = false
			_apply_frame()
			animation_finished.emit(current_animation)
			return
	elif frame_index < 0:
		if clip.loop:
			frame_index = posmod(frame_index, count)
		else:
			frame_index = 0
			is_playing = false
			_apply_frame()
			animation_finished.emit(current_animation)
			return
	_apply_frame()


func _apply_frame() -> void:
	var clip := get_clip(current_animation)
	if clip == null or clip.frames.is_empty():
		return
	var rect := clip.frame_rect(frame_index)
	if rect.size.x <= 0.0 or rect.size.y <= 0.0:
		return
	region_rect = rect
	flip_h = global_flip_h != clip.flip_h
	flip_v = global_flip_v != clip.flip_v
	clip_frame_changed.emit(frame_index)
