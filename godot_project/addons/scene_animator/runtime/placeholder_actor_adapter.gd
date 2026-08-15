@tool
class_name PlaceholderActorAdapter
extends SceneActorAdapter

## Drop-in actor for cutscenes / test scenes and the tutorial demo. Owns a
## Marker3D body (created on demand) so move_to / look_at work with no game
## code. request_action emits a configurable event sequence (`impact`, ...) then
## signals `action_completed`, so ActionBeats + WaitForEventBeats chain
## correctly. Success is modelled, not deadline-gated, so it completes.

@export var actor_display_name := ""
@export var action_events: Array[StringName] = []
@export var action_event_delay := 0.18

var _event_timer: Timer
var _completion_timer: Timer


func _ready() -> void:
	if body == null:
		var marker := Marker3D.new()
		marker.name = &"Body"
		add_child(marker)
		if Engine.is_editor_hint():
			var owner_node := self.get_owner()
			if owner_node == null:
				owner_node = self
			marker.owner = owner_node
		body = marker
	if not Engine.is_editor_hint():
		process_mode = Node.PROCESS_MODE_INHERIT


func move_to(target: Node3D, arrival_radius: float, locomotion_mode: StringName) -> void:
	_move_target = target
	_move_radius = arrival_radius
	_move_mode = locomotion_mode
	set_process(true)


func look_at_target(target: Node3D) -> void:
	if target == null or body == null:
		look_at_completed.emit(target)
		return
	var to_target := target.global_transform.origin - body.global_transform.origin
	if to_target.length() < 0.0001:
		look_at_completed.emit(target)
		return
	var target_quat := Basis.looking_at(to_target, Vector3.UP).get_rotation_quaternion()
	body.quaternion = body.quaternion.slerp(target_quat, 1.0)
	look_at_completed.emit(target)


func request_action(action_id: StringName, target: Node3D, context: Dictionary = {}) -> void:
	_action_id = action_id
	_busy = true

	_event_timer = Timer.new()
	_event_timer.one_shot = true
	_event_timer.wait_time = action_event_delay
	_event_timer.timeout.connect(_on_emit_events)
	add_child(_event_timer)

	_completion_timer = Timer.new()
	_completion_timer.one_shot = true
	_completion_timer.wait_time = action_duration
	_completion_timer.timeout.connect(_on_action_succeeded)
	add_child(_completion_timer)

	_event_timer.start()
	_completion_timer.start()


func cancel_current_action() -> void:
	if _event_timer != null:
		_event_timer.stop()
	if _completion_timer != null:
		_completion_timer.stop()
	if _busy:
		_busy = false
		action_failed.emit(_action_id, &"cancelled")


func _on_emit_events() -> void:
	for event_name in action_events:
		action_event_emitted.emit(event_name, {})


func _on_action_succeeded() -> void:
	if _busy:
		_busy = false
		action_completed.emit(_action_id)
