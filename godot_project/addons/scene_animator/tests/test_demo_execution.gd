class_name TestDemoExecution
extends RefCounted

## End-to-end demo contract suite. Verifies the runnable demo scene drives the
## full runtime to a clean completion and that the shipped template plans are
## validator-clean (no errors).

const DEMO_SCENE := "res://addons/scene_animator/demo/demo_scene.tscn"
const DEMO_PLAN := "res://addons/scene_animator/demo/demo_scene_plan.tres"
const STARTER_PLAN := "res://addons/scene_animator/templates/starter_scene_plan.tres"

static var _demo_counter := 0

var _ctx: SceneAnimatorTestContext


func run() -> SceneAnimatorTestResult:
	var result := SceneAnimatorTestResult.new()
	result.suite_name = &"test_demo_execution"
	_ctx = SceneAnimatorTestContext.new(result)
	var started_ms := Time.get_ticks_msec()

	await _test_demo_plan_is_valid()
	await _test_demo_scene_plays_to_completion()
	await _test_starter_template_is_valid()

	result.duration_ms = Time.get_ticks_msec() - started_ms
	return result


func _make_test_root() -> Node:
	_demo_counter += 1
	var test_root := Node.new()
	test_root.name = "DemoTestRoot_%d" % _demo_counter
	(Engine.get_main_loop() as SceneTree).root.add_child(test_root)
	return test_root


func _teardown_root(test_root: Node) -> void:
	test_root.queue_free()
	await (Engine.get_main_loop() as SceneTree).process_frame


func _test_demo_plan_is_valid() -> void:
	var plan := load(DEMO_PLAN) as ScenePlan
	if not _ctx.is_true(plan != null, &"demo.plan_loads", "demo_scene_plan.tres must load."):
		return
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(result.is_valid(), &"demo.plan_valid", "The demo plan must be validator-clean (no errors).")


func _test_demo_scene_plays_to_completion() -> void:
	var packed := load(DEMO_SCENE) as PackedScene
	if not _ctx.is_true(packed != null, &"demo.scene_loads", "demo_scene.tscn must load."):
		return

	var tree := Engine.get_main_loop() as SceneTree
	var test_root := _make_test_root()

	var scene := packed.instantiate() as DemoSceneController
	_ctx.is_true(scene != null, &"demo.scene_root", "demo_scene.tscn root must be a DemoSceneController.")
	scene.auto_play = false
	test_root.add_child(scene)

	var finished := {"count": 0}
	var failed := {"reason": &"", "details": {}}
	scene.demo_finished.connect(func() -> void:
		finished["count"] += 1
	)
	scene.demo_failed.connect(func(reason: StringName, details: Dictionary) -> void:
		failed["reason"] = reason
		failed["details"] = details
	)

	scene.play_demo()
	await tree.process_frame

	_ctx.equals(finished["count"], 1, &"demo.completes", "The demo scene must finish exactly once.")
	_ctx.equals(failed["reason"], &"", &"demo.no_failure", "The demo must not fail.")
	_ctx.equals(scene.dialogue_played, 3, &"demo.plays_all_lines", "All three dialogue lines must play.")

	await _teardown_root(test_root)


func _test_starter_template_is_valid() -> void:
	var plan := load(STARTER_PLAN) as ScenePlan
	if not _ctx.is_true(plan != null, &"template.loads", "starter_scene_plan.tres must load."):
		return
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(result.is_valid(), &"template.valid", "The starter template must be validator-clean.")
