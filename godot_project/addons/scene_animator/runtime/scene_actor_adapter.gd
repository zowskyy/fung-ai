@tool
class_name SceneActorAdapter
extends Node

## Generic contract between the Scene Animator and any character/actor impl.
##
## This base provides functional deadline-driven defaults that operate on an
## exported `body` Node3D, so a plan can drive a placeholder actor without game
## code. Real character adapters subclass and override `move_to`,
## `look_at_target`, `request_action`, and `cancel_current_action` to talk to
## their animation driver / controller.
##
## Deadline semantics: the base `request_action` starts an action deadline
## timer; if a subclass does not override and emit `action_completed` first,
## the action fails with `action_timeout`. This makes missing completions
## observable rather than silently blocking a scene.

signal action_event_emitted(event_name: StringName, payload: Variant)
signal action_completed(action_id: StringName)
signal action_failed(action_id: StringName, reason: StringName)
signal destination_reached(target: Node3D)
signal look_at_completed(target: Node3D)

## Node whose transform is driven by the default implementations.
@export var body: Node3D
@export var move_speed := 4.5
@export var action_duration := 0.35

var _move_target: Node3D = null
var _move_radius := 0.0
var _move_mode: StringName = &"walk"
var _action_timer: Timer = null
var _action_id: StringName = &""
var _busy := false


func move_to(target: Node3D, arrival_radius: float, locomotion_mode: StringName) -> void:
	if target == null:
		action_failed.emit(&"", &"missing_target")
		return
	_move_target = target
	_move_radius = arrival_radius
	_move_mode = locomotion_mode
	set_process(true)


func look_at_target(target: Node3D) -> void:
	if target == null or body == null:
		look_at_completed.emit(target)
		return
	body.look_at(target.global_transform.origin, Vector3.UP)
	look_at_completed.emit(target)


## Base implementation: start an action deadline. Subclasses override to drive
## real animation and emit `action_completed` / `action_failed` themselves.
func request_action(action_id: StringName, target: Node3D, context: Dictionary = {}) -> void:
	_action_id = action_id
	_ensure_action_timer()
	_busy = true
	_action_timer.wait_time = action_duration
	_action_timer.start()


func cancel_current_action() -> void:
	set_process(false)
	if _move_target != null:
		_move_target = null
	_ensure_action_timer(false)
	if _busy:
		_busy = false
		action_failed.emit(_action_id, &"cancelled")


func _ensure_action_timer(create: bool = true) -> void:
	if not create and _action_timer != null:
		_action_timer.stop()
		return
	if _action_timer == null:
		_action_timer = Timer.new()
		_action_timer.one_shot = true
		_action_timer.timeout.connect(_on_action_timer_timeout)
		add_child(_action_timer)


## Deadline expiry: the action did not signal completion in time.
func _on_action_timer_timeout() -> void:
	if _busy:
		_busy = false
		action_failed.emit(_action_id, &"action_timeout")


func _position() -> Vector3:
	if body != null and is_instance_valid(body):
		return body.global_transform.origin
	return Vector3.ZERO


func _set_position(p: Vector3) -> void:
	if body != null and is_instance_valid(body):
		var t := body.global_transform
		t.origin = p
		body.global_transform = t


func _speed_for_mode() -> float:
	if _move_mode == "run":
		return move_speed * 1.6
	return move_speed


func _process(delta: float) -> void:
	if _move_target == null or not is_instance_valid(_move_target):
		set_process(false)
		return
	var here := _position()
	var to_target := _move_target.global_transform.origin - here
	if to_target.length() <= _move_radius:
		_settled_move()
		return
	var step := to_target.normalized() * _speed_for_mode() * delta
	if step.length() >= to_target.length():
		_set_position(here + to_target)
		_settled_move()
	else:
		_set_position(here + step)


func _settled_move() -> void:
	_move_target = null
	set_process(false)
	destination_reached.emit(null)
