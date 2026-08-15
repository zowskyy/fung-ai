class_name CharacterAnimationDriver
extends Node
## Bridges gameplay state into an AnimationTree.
##
## The plugin never owns movement. A controller (CharacterBody2D, enemy AI, a
## brawler motor, or C# gameplay code) feeds facts to this node and it writes
## AnimationTree parameters and requests states. No physics here.

signal state_requested(state: StringName)

@export var profile: CharacterAnimationProfile
@export var animation_tree: AnimationTree
@export var visuals: Node2D
@export var run_speed := 320.0

var _last_grounded := false
var _last_facing_right := true

func _ready() -> void:
	if animation_tree != null:
		animation_tree.active = true
	_reapply_facing()


func has_tree() -> bool:
	return animation_tree != null


## Main entry point. Called every physics frame by the gameplay controller.
func update_locomotion(body_velocity: Vector2, grounded: bool, crouching: bool, facing_right: bool) -> void:
	if animation_tree == null:
		return
	var normalized_speed := clampf(absf(body_velocity.x) / maxf(run_speed, 0.001), 0.0, 1.0)
	animation_tree.set("parameters/Locomotion/blend_position", normalized_speed)
	animation_tree.set("parameters/conditions/grounded", grounded)
	animation_tree.set("parameters/conditions/crouching", crouching)
	animation_tree.set("parameters/conditions/rising", not grounded and body_velocity.y < 0.0)
	animation_tree.set("parameters/conditions/falling", not grounded and body_velocity.y >= 0.0)
	animation_tree.set("parameters/conditions/standing", grounded and not crouching)
	var moving := absf(body_velocity.x) > _epsilon()
	animation_tree.set("parameters/conditions/moving", moving)
	animation_tree.set("parameters/conditions/stopped", not moving)
	if not _last_grounded and grounded:
		request_state(&"Land")
	_last_grounded = grounded
	_set_facing(facing_right)


## Consumes a CharacterAnimationState snapshot (useful for AI / top-down).
func update_from_state(state: CharacterAnimationState) -> void:
	update_locomotion(state.velocity, state.grounded, state.crouching, state.facing_right)


## Asks the state machine to travel to a state (Land, Attack1, Hurt, ...).
func request_state(state_name: StringName) -> void:
	if animation_tree == null:
		return
	var playback: Variant = animation_tree.get("parameters/playback")
	if playback is AnimationNodeStateMachinePlayback:
		playback.travel(String(state_name))
	state_requested.emit(state_name)


func current_state_name() -> StringName:
	if animation_tree == null:
		return &""
	var playback: Variant = animation_tree.get("parameters/playback")
	if playback is AnimationNodeStateMachinePlayback:
		return StringName(playback.get_current_node())
	return &""


func _epsilon() -> float:
	if profile != null:
		return profile.speed_epsilon
	return 5.0


func _set_facing(facing_right: bool) -> void:
	if visuals == null or _last_facing_right == facing_right:
		return
	_last_facing_right = facing_right
	var scale := visuals.scale
	scale.x = absf(scale.x) * (1.0 if facing_right else -1.0)
	visuals.scale = scale


func _reapply_facing() -> void:
	if visuals == null:
		return
	var scale := visuals.scale
	scale.x = absf(scale.x) * (1.0 if _last_facing_right else -1.0)
	visuals.scale = scale
