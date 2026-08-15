class_name DemoSceneController
extends Node3D

## Runnable tutorial demo. Builds the SceneAnimator runtime graph at runtime,
## registers the dialogue effects the demo plan references, drives the plan
## through a real SceneDirector, and reports completion.
##
## Standalone run:
##   godot --path godot_project --headless demo/demo_scene.tscn
## Driven by tests: set auto_play = false before adding to the tree, then call
## play_demo() once signals are connected.

signal demo_finished
signal demo_failed(reason: StringName, details: Dictionary)

@export var plan_path := "res://addons/scene_animator/demo/demo_scene_plan.tres"
@export var auto_play := true

var dialogue_played := 0

var _director: SceneDirector
var _bindings: SceneBindings


func _ready() -> void:
	if Engine.is_editor_hint():
		return
	_build_runtime()
	if auto_play:
		play_demo()


func play_demo() -> void:
	if _director == null:
		_build_runtime()
	_director.start_scene()


func _build_runtime() -> void:
	_director = SceneDirector.new()
	_director.name = &"Director"
	add_child(_director)

	_bindings = SceneBindings.new()
	_bindings.name = &"Bindings"
	add_child(_bindings)

	var registry := SceneMechanicsRegistry.new()
	registry.name = &"Mechanics"
	_bindings.add_child(registry)
	_bindings.mechanics_registry = registry
	_register_effects(registry)

	var hero := PlaceholderActorAdapter.new()
	hero.name = &"Hero"
	var villain := PlaceholderActorAdapter.new()
	villain.name = &"Villain"
	_bindings.add_child(hero)
	_bindings.add_child(villain)
	_bindings.actor_nodes[&"hero"] = NodePath("Hero")
	_bindings.actor_nodes[&"villain"] = NodePath("Villain")

	_director.plan = load(plan_path) as ScenePlan
	_director.bindings = _bindings
	_director.scene_finished.connect(_on_demo_finished)
	_director.scene_failed.connect(_on_demo_failed)


func _register_effects(registry: SceneMechanicsRegistry) -> void:
	registry.register_effect(&"demo_open", _play_line_demo_open)
	registry.register_effect(&"demo_intro", _play_line_demo_intro)
	registry.register_effect(&"demo_outro", _play_line_demo_outro)


func _play_line_demo_open(payload: Dictionary) -> void:
	dialogue_played += 1
	print("[scene_animator:demo] Hero: \"Welcome to the Quiet Cave.\"")
	_finish_line(payload)


func _play_line_demo_intro(payload: Dictionary) -> void:
	dialogue_played += 1
	print("[scene_animator:demo] Hero: \"That shadow there? That is the Keeper.\"")
	_finish_line(payload)


func _play_line_demo_outro(payload: Dictionary) -> void:
	dialogue_played += 1
	print("[scene_animator:demo] Keeper: \"Leave the amber. Leave, and stay alive.\"")
	_finish_line(payload)


## Dialogue beats wait for the speaker's action_event_emitted; completing them
## here keeps the demo deterministic and free of timing dependencies.
func _finish_line(payload: Dictionary) -> void:
	var speaker := payload.get("speaker") as SceneActorAdapter
	if speaker != null:
		speaker.action_event_emitted.emit(&"dialogue_finished", {})


func _on_demo_finished() -> void:
	print("[scene_animator:demo] Scene finished after %d dialogue line(s)." % dialogue_played)
	demo_finished.emit()
	_quit_if_standalone(0)


func _on_demo_failed(reason: StringName, details: Dictionary) -> void:
	push_error("[scene_animator:demo] Scene failed: %s %s" % [reason, JSON.stringify(details)])
	demo_failed.emit(reason, details)
	_quit_if_standalone(1)


func _quit_if_standalone(code: int) -> void:
	if not Engine.is_editor_hint() and get_tree() != null and get_tree().current_scene == self:
		get_tree().quit(code)
