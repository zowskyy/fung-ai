class_name PlayerController
extends CharacterBody2D
## Reference CharacterBody2D controller for the demo.
##
## Implements the recommended physics flow: read input, resolve crouch, apply
## gravity + horizontal movement, consume buffered jump, MoveAndSlide(), then
## read floor state, update facing, and finally feed the animation plugin.
##
## The plugin never owns physics: this script only supplies the
## CharacterAnimationDriver with velocity / grounded / crouching / facing.

@export_group("Movement")
@export var run_speed := 320.0
@export var crouch_speed_multiplier := 0.45
@export var ground_acceleration := 2400.0
@export var ground_deceleration := 2800.0
@export var air_acceleration := 1200.0
@export var gravity := 1400.0
@export var max_fall_speed := 900.0

@export_group("Jump")
@export var jump_velocity := -500.0
@export var coyote_time := 0.10
@export var jump_buffer_time := 0.12
@export var jump_release_gravity_multiplier := 2.2

@export_group("Nodes")
@export var standing_collider: CollisionShape2D
@export var crouching_collider: CollisionShape2D
@export var stand_clearance: ShapeCast2D
@export var visuals: Node2D
@export var animation_driver: CharacterAnimationDriver

signal landed()
signal jumped()
signal crouch_changed(crouching: bool)

var _was_on_floor := false
var _is_crouching := false
var _facing_right := true
var _coyote_timer := 0.0
var _jump_buffer_timer := 0.0


func _ready() -> void:
	set_crouching(false, true)


func _physics_process(delta: float) -> void:
	_read_jump_input(delta)
	_update_ground_timers(delta)
	_update_crouch_state()
	_apply_gravity(delta)
	_apply_horizontal_movement(delta)
	_try_jump()
	move_and_slide()
	_handle_landing()
	_update_facing()
	_update_animation()


func _read_jump_input(delta: float) -> void:
	if Input.is_action_just_pressed("jump"):
		_jump_buffer_timer = jump_buffer_time
	else:
		_jump_buffer_timer = maxf(0.0, _jump_buffer_timer - delta)


func _update_ground_timers(delta: float) -> void:
	if is_on_floor():
		_coyote_timer = coyote_time
	else:
		_coyote_timer = maxf(0.0, _coyote_timer - delta)


func _update_crouch_state() -> void:
	var wants_to_crouch := Input.is_action_pressed("crouch")
	if not wants_to_crouch and not _can_stand():
		wants_to_crouch = true
	set_crouching(wants_to_crouch)


func _can_stand() -> bool:
	if stand_clearance == null:
		return true
	stand_clearance.force_shapecast_update()
	return not stand_clearance.is_colliding()


func set_crouching(value: bool, force := false) -> void:
	if not force and _is_crouching == value:
		return
	_is_crouching = value
	if standing_collider != null:
		standing_collider.disabled = _is_crouching
	if crouching_collider != null:
		crouching_collider.disabled = not _is_crouching
	if not force:
		crouch_changed.emit(_is_crouching)


func _apply_gravity(delta: float) -> void:
	if is_on_floor():
		return
	var gravity_multiplier := 1.0
	if velocity.y < 0.0 and not Input.is_action_pressed("jump"):
		gravity_multiplier = jump_release_gravity_multiplier
	velocity.y = minf(velocity.y + gravity * gravity_multiplier * delta, max_fall_speed)


func _apply_horizontal_movement(delta: float) -> void:
	var input := Input.get_axis("move_left", "move_right")
	var target_speed := input * run_speed
	if _is_crouching:
		target_speed *= crouch_speed_multiplier
	var has_input := not is_zero_approx(input)
	var acceleration: float
	if is_on_floor():
		acceleration = ground_acceleration if has_input else ground_deceleration
	else:
		acceleration = air_acceleration
	velocity.x = move_toward(velocity.x, target_speed, acceleration * delta)


func _try_jump() -> void:
	var can_jump := is_on_floor() or _coyote_timer > 0.0
	if _jump_buffer_timer <= 0.0 or not can_jump or _is_crouching:
		return
	velocity.y = jump_velocity
	_jump_buffer_timer = 0.0
	_coyote_timer = 0.0
	jumped.emit()


func _handle_landing() -> void:
	if not _was_on_floor and is_on_floor():
		landed.emit()
	_was_on_floor = is_on_floor()


func _update_facing() -> void:
	if absf(velocity.x) < 1.0:
		return
	var should_face_right := velocity.x > 0.0
	if should_face_right == _facing_right:
		return
	_facing_right = should_face_right
	if visuals != null:
		var scale := visuals.scale
		scale.x = absf(scale.x) * (1.0 if _facing_right else -1.0)
		visuals.scale = scale


func _update_animation() -> void:
	if animation_driver == null:
		return
	animation_driver.update_locomotion(velocity, is_on_floor(), _is_crouching, _facing_right)
