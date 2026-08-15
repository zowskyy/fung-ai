class_name FakeActorAdapter
extends SceneActorAdapter

## Recording actor adapter. Tracks dialogue / motion / action requests and call
## order, and can be switched into a failure mode for controlled-failure tests.

var actor_id: StringName
var move_calls: Array[Dictionary] = []
var look_at_calls: Array[Dictionary] = []
var action_calls: Array[Dictionary] = []
var cancel_calls := 0
var fail_actions := false


func setup_fake(id: StringName) -> void:
	actor_id = id


func move_to(target: Node3D, arrival_radius: float, locomotion_mode: StringName) -> void:
	move_calls.append({
		"target": target,
		"arrival_radius": arrival_radius,
		"locomotion_mode": locomotion_mode,
	})
	if fail_actions:
		action_failed.emit(&"", &"fake_action_failure")
	else:
		destination_reached.emit(target)


func look_at_target(target: Node3D) -> void:
	look_at_calls.append({"target": target})
	look_at_completed.emit(target)


func request_action(action_id: StringName, target: Node3D, context: Dictionary = {}) -> void:
	action_calls.append({
		"action_id": action_id,
		"target": target,
		"context": context.duplicate(false),
	})
	if fail_actions:
		action_failed.emit(action_id, &"fake_action_failure")
	else:
		action_completed.emit(action_id)


func cancel_current_action() -> void:
	cancel_calls += 1


## Test seam: emit the event that DialogueBeatRunner treats as completion.
func finish_dialogue() -> void:
	action_event_emitted.emit(&"dialogue_finished", {})
