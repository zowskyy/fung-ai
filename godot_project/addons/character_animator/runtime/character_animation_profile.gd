@tool
class_name CharacterAnimationProfile
extends Resource
## Reusable definition of what a character's animations mean.
##
## The plugin's graph generator and validator both read this resource, so the
## same profile can regenerate a consistent AnimationTree for many characters
## that happen to use different source clip names.

@export_category("Scene References")
@export var animator_path: NodePath
@export var animation_player_path: NodePath
@export var visuals_path: NodePath

@export_category("Locomotion Clips")
@export var idle: StringName = &"idle"
@export var walk: StringName = &"walk"
@export var run: StringName = &"run"
@export var jump: StringName = &"jump"
@export var fall: StringName = &"fall"
@export var land: StringName = &"land"

@export_category("Stance Clips")
@export var crouch_idle: StringName = &"crouch_idle"
@export var crouch_move: StringName = &"crouch_walk"

@export_category("Action Clips")
@export var attack_1: StringName = &"attack_1"
@export var hurt: StringName = &"hurt"

@export_category("Movement Tuning")
@export_range(0.0, 1.0) var walk_point := 0.45
@export_range(0.0, 1.0) var run_point := 1.0
@export_range(0.0, 1.0) var transition_blend_time := 0.12
@export var speed_epsilon := 5.0


func animation_names() -> PackedStringArray:
	var names := PackedStringArray()
	for name in [idle, walk, run, jump, fall, land, crouch_idle, crouch_move, attack_1, hurt]:
		if name != &"":
			names.append(name)
	return names


func required_animation_names() -> PackedStringArray:
	var names := PackedStringArray()
	for name in [idle, run, jump, fall]:
		if name != &"":
			names.append(name)
	return names


func has_clip_role(clip_name: StringName) -> bool:
	return (
		idle == clip_name or walk == clip_name or run == clip_name or jump == clip_name
		or fall == clip_name or land == clip_name or crouch_idle == clip_name
		or crouch_move == clip_name or attack_1 == clip_name or hurt == clip_name
	)
