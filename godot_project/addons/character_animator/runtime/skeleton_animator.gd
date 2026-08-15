class_name SkeletonAnimator
extends Node
## Plays BoneClip resources on a CharacterSkeleton node.
##
## Finds the skeleton through skeleton_path, then as a child, then as the
## parent, so it works when placed anywhere in a character tree.

signal clip_started(clip: StringName)
signal clip_finished(clip: StringName)

@export var skeleton_path: NodePath
@export var clips: Dictionary = {}
@export var initial_clip: StringName = &""
@export var auto_play: bool = true
@export var speed_scale: float = 1.0

var current_clip: StringName = &""
var is_playing: bool = false
var paused: bool = false

var _time: float = 0.0
var _skeleton: CharacterSkeleton = null


func _ready() -> void:
	_skeleton = _find_skeleton()
	if auto_play and initial_clip != &"":
		play(initial_clip)


func has_clip(clip_name: StringName) -> bool:
	return clips.has(clip_name)


func get_clip(clip_name: StringName) -> BoneClip:
	return clips.get(clip_name) as BoneClip


func clip_names() -> PackedStringArray:
	var names := PackedStringArray()
	for clip_name in clips:
		names.append(clip_name)
	return names


func play(clip_name: StringName, from_begin: bool = true) -> void:
	var clip := get_clip(clip_name)
	if clip == null:
		push_warning("SkeletonAnimator.play: no clip named '%s'." % clip_name)
		return
	current_clip = clip_name
	is_playing = true
	paused = false
	if from_begin:
		_time = 0.0
	clip_started.emit(clip_name)


func stop() -> void:
	is_playing = false
	_time = 0.0


func pause() -> void:
	paused = true


func resume() -> void:
	if is_playing:
		paused = false


func _process(delta: float) -> void:
	advance(delta)


## Advances playback by delta seconds. Extracted from _process so tests and
## deterministic tools can step the animation without waiting for frames.
func advance(delta: float) -> void:
	if not is_playing or paused:
		return
	var clip := get_clip(current_clip)
	if clip == null:
		return
	var duration := clip.duration()
	if duration <= 0.0:
		return
	_time += delta * speed_scale
	if _time > duration:
		if clip.loop:
			_time = fmod(_time, duration)
		else:
			_time = duration
			_apply_at(clip, _time)
			is_playing = false
			clip_finished.emit(current_clip)
			return
	_apply_at(clip, _time)


func _apply_at(clip: BoneClip, time: float) -> void:
	if _skeleton == null:
		return
	var out := {}
	clip.sample(time, out)
	for bone_name in out:
		var key: BoneKey = out[bone_name]
		_skeleton.apply_pose(bone_name, key.position, key.rotation, key.scale)


func _find_skeleton() -> CharacterSkeleton:
	if skeleton_path != NodePath():
		var node := get_node_or_null(skeleton_path)
		if node is CharacterSkeleton:
			return node
	for child in get_children():
		if child is CharacterSkeleton:
			return child
	var parent := get_parent()
	if parent is CharacterSkeleton:
		return parent
	if parent != null:
		for sibling in parent.get_children():
			if sibling is CharacterSkeleton:
				return sibling
	return null
