@tool
class_name SceneMechanicsRegistry
extends Node

## Runtime registry of mechanics a plan can invoke: encounter spawners, camera
## mode providers, state setters, and audio/VFX event hooks. Populated by the
## bindings or by a game-specific bootstrap. All lookups are by stable ID so a
## plan never hardcodes node types.

signal encounter_spawned(encounter_id: StringName, spawner: Node)
signal encounter_cleared(encounter_id: StringName)
signal state_changed(target: Node, state_id: StringName)

## encounter_id -> Callable(spawn_marker_ids: Array[NodePath]) -> Node
var _encounter_spawners: Dictionary = {}
## camera_mode_id -> Callable(focus_target: Node3D, blend_seconds: float) -> SceneCameraAdapter
var _camera_providers: Dictionary = {}
## state_id -> Callable(target: Node)
var _state_setters: Dictionary = {}
## effect_id -> Callable(payload)
var _effects: Dictionary = {}
## condition_id -> Callable() -> bool
var _condition_evaluators: Dictionary = {}


func register_encounter_spawner(encounter_id: StringName, spawner: Callable) -> void:
	_encounter_spawners[encounter_id] = spawner


func has_encounter(encounter_id: StringName) -> bool:
	return _encounter_spawners.has(encounter_id)


func spawn_encounter(encounter_id: StringName, marker_paths: Array[NodePath]) -> Node:
	if not _encounter_spawners.has(encounter_id):
		return null
	var spawner: Callable = _encounter_spawners[encounter_id]
	if spawner.get_argument_count() != 1:
		return null
	var result = spawner.call(marker_paths)
	if result is Node:
		var node := result as Node
		encounter_spawned.emit(encounter_id, node)
		return node
	return null


func register_camera_provider(mode_id: StringName, provider: Callable) -> void:
	_camera_providers[mode_id] = provider


func has_camera_mode(mode_id: StringName) -> bool:
	return _camera_providers.has(mode_id)


func acquire_camera(mode_id: StringName, focus_target: Node3D, blend_seconds: float) -> SceneCameraAdapter:
	if not _camera_providers.has(mode_id):
		return null
	var provider: Callable = _camera_providers[mode_id]
	if provider.get_argument_count() > 0:
		var result = provider.call(focus_target, blend_seconds)
		if result is SceneCameraAdapter:
			return result
	return null


func register_state_setter(state_id: StringName, setter: Callable) -> void:
	_state_setters[state_id] = setter


func has_state_setter(state_id: StringName) -> bool:
	return _state_setters.has(state_id)


func set_state(target: Node, state_id: StringName) -> bool:
	if not _state_setters.has(state_id):
		return false
	var setter: Callable = _state_setters[state_id]
	if setter.get_argument_count() >= 1:
		setter.call(target)
	state_changed.emit(target, state_id)
	return true


func register_effect(effect_id: StringName, effect: Callable) -> void:
	_effects[effect_id] = effect


func has_effect(effect_id: StringName) -> bool:
	return _effects.has(effect_id)


func play_effect(effect_id: StringName, payload: Dictionary = {}) -> void:
	if not _effects.has(effect_id):
		return
	var effect: Callable = _effects[effect_id]
	effect.call(payload)
	effects_requested.emit(effect_id, payload)


func register_condition_evaluator(condition_id: StringName, evaluator: Callable) -> void:
	_condition_evaluators[condition_id] = evaluator


func has_condition(condition_id: StringName) -> bool:
	return _condition_evaluators.has(condition_id)


func evaluate_condition(condition_id: StringName) -> bool:
	if not _condition_evaluators.has(condition_id):
		return false
	var evaluator: Callable = _condition_evaluators[condition_id]
	if evaluator.get_argument_count() == 0:
		var result = evaluator.call()
		return bool(result)
	return false


signal effects_requested(effect_id: StringName, payload: Dictionary)
