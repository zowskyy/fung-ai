class_name CharacterAnimationState
extends RefCounted
## A plain snapshot of the gameplay facts the animation plugin consumes.
##
## Movement controllers (platformer, top-down, AI, C# motor) build one of
## these per frame and hand it to CharacterAnimationDriver.update_from_state.

var move_input: Vector2 = Vector2.ZERO
var velocity: Vector2 = Vector2.ZERO
var grounded: bool = false
var crouching: bool = false
var facing_right: bool = true
var action: StringName = &"none"
var action_locked: bool = false


func normalized_speed(run_speed: float) -> float:
	return clampf(absf(velocity.x) / maxf(run_speed, 0.001), 0.0, 1.0)


func is_falling() -> bool:
	return not grounded and velocity.y >= 0.0


func is_rising() -> bool:
	return not grounded and velocity.y < 0.0
