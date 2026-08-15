class_name TestRuntimeExecution
extends RefCounted

## Behavioral contract suite for the Scene Animator runtime. Exercises the
## dialogue actor-binding contract fixed in Phase 0 plus core SceneDirector
## sequencing, using recording fakes and the serialized .tres fixtures.

const FIXTURE_VALID := "res://addons/scene_animator/tests/fixtures/valid_linear_scene_plan.tres"
const FIXTURE_MISSING_SPEAKER := "res://addons/scene_animator/tests/fixtures/invalid_missing_speaker_plan.tres"
const FIXTURE_UNKNOWN_TARGET := "res://addons/scene_animator/tests/fixtures/invalid_unknown_target_plan.tres"

static var _runtime_counter := 0

var _ctx: SceneAnimatorTestContext


func run() -> SceneAnimatorTestResult:
	var result := SceneAnimatorTestResult.new()
	result.suite_name = &"test_runtime_execution"
	_ctx = SceneAnimatorTestContext.new(result)
	var started_ms := Time.get_ticks_msec()

	await _test_valid_linear_plan()
	await _test_missing_speaker_fails()
	await _test_unknown_target_fails()
	await _test_terminal_failure_blocks_later_beats()
	await _test_empty_plan_deterministic()

	result.duration_ms = Time.get_ticks_msec() - started_ms
	return result


# --------------------------------------------------------------------------- #
# Runtime scaffolding
# --------------------------------------------------------------------------- #

## Builds an isolated runtime under a fresh parent node so per-test cleanup
## cannot contaminate later cases. Director navigates first_enabled_beat() then
## next_beat_id, terminal when next_beat_id is empty.
func _make_runtime() -> Dictionary:
	var tree := Engine.get_main_loop() as SceneTree
	_runtime_counter += 1
	var test_root := Node.new()
	test_root.name = "TestRoot_%d" % _runtime_counter
	tree.root.add_child(test_root)

	var bindings := SceneBindings.new()
	bindings.name = "Bindings"
	var registry := FakeMechanicsRegistry.new()
	registry.name = "FakeMechanics"
	bindings.mechanics_registry = registry
	bindings.add_child(registry)

	var hero := FakeActorAdapter.new()
	hero.name = "Hero"
	hero.setup_fake(&"hero")
	var villain := FakeActorAdapter.new()
	villain.name = "Villain"
	villain.setup_fake(&"villain")

	test_root.add_child(bindings)
	bindings.add_child(hero)
	bindings.add_child(villain)
	bindings.actor_nodes[&"hero"] = NodePath("Hero")
	bindings.actor_nodes[&"villain"] = NodePath("Villain")

	var director := SceneDirector.new()
	director.name = "Director"
	test_root.add_child(director)

	var terminal: Dictionary = {
		"finished": 0,
		"failed": 0,
		"failed_reason": &"",
		"failed_details": {},
	}
	director.scene_finished.connect(func() -> void:
		terminal["finished"] += 1
	)
	director.scene_failed.connect(func(reason: StringName, details: Dictionary) -> void:
		terminal["failed"] += 1
		terminal["failed_reason"] = reason
		terminal["failed_details"] = details
	)

	return {
		"tree": tree,
		"test_root": test_root,
		"bindings": bindings,
		"registry": registry,
		"hero": hero,
		"villain": villain,
		"director": director,
		"terminal": terminal,
	}


func _teardown(runtime: Dictionary) -> void:
	var director: SceneDirector = runtime["director"]
	director.stop_scene()
	(runtime["test_root"] as Node).queue_free()
	await (Engine.get_main_loop() as SceneTree).process_frame


func _start(runtime: Dictionary, plan: ScenePlan) -> void:
	var director: SceneDirector = runtime["director"]
	director.plan = plan
	director.bindings = runtime["bindings"]
	director.start_scene()


# --------------------------------------------------------------------------- #
# Contract 1-3, 6-11: valid linear plan
# --------------------------------------------------------------------------- #

func _test_valid_linear_plan() -> void:
	var runtime := _make_runtime()
	var plan := load(FIXTURE_VALID) as ScenePlan
	if not _ctx.is_true(plan != null, &"fixture.valid_plan_loads", "valid_linear_scene_plan.tres must load"):
		await _teardown(runtime)
		return

	var registry: FakeMechanicsRegistry = runtime["registry"]
	registry.register_effect(&"line_a", func(payload: Dictionary) -> void: pass)
	registry.register_effect(&"line_b", func(payload: Dictionary) -> void: pass)

	var bindings: SceneBindings = runtime["bindings"]
	var hero: FakeActorAdapter = runtime["hero"]
	var villain: FakeActorAdapter = runtime["villain"]

	var resolved: Dictionary = {"count": 0}
	bindings.actor_resolved.connect(func(_actor_id: StringName, _adapter: SceneActorAdapter) -> void:
		resolved["count"] += 1
	)

	_start(runtime, plan)

	# First beat ran exactly once (contract 10).
	_ctx.equals(registry.calls.size(), 1, &"runtime.effect_once_per_beat", "First dialogue beat must invoke play_effect exactly once.")
	if registry.calls.is_empty():
		await _teardown(runtime)
		return

	# Primary empty-target proof (contract 3): the context target is null.
	_ctx.equals(registry.calls[0]["context"]["target_actor"], null, &"dialogue.empty_target_allowed", "An empty target_actor_id must produce a null target_actor.")
	# Supplemental: only the speaker lookup resolved.
	_ctx.equals(resolved["count"], 1, &"dialogue.empty_target_skips_lookup", "Empty target must not trigger a second actor resolution.")
	# Speaker resolves (contract 1).
	_ctx.equals(registry.calls[0]["context"]["speaker"], hero, &"dialogue.speaker_resolves", "Speaker must resolve by speaker_actor_id.")
	# Context beat id preserved (contract 6).
	_ctx.equals(registry.calls[0]["context"]["scene_beat_id"], &"dialogue_a", &"dialogue.context_beat_id", "Effect context must preserve the beat id.")
	# New key present, legacy key absent (contracts 8, 9).
	_ctx.is_true(registry.calls[0]["context"].has("target_actor"), &"dialogue.target_key_present", "Effect context must expose target_actor.")
	_ctx.is_true(not registry.calls[0]["context"].has("target"), &"dialogue.no_legacy_target", "Effect context must not expose the legacy target key.")

	# Complete dialogue_a; dialogue_b runs synchronously through next_beat_id.
	hero.finish_dialogue()

	# Exactly one additional effect call after the first completion (contract 10).
	_ctx.equals(registry.calls.size(), 2, &"runtime.effect_once_per_beat", "Second dialogue beat must add exactly one effect call.")
	if registry.calls.size() < 2:
		await _teardown(runtime)
		return

	# Declared progression (contract 11) via next_beat_id navigation.
	_ctx.equals(registry.calls[0]["effect_id"], &"line_a", &"runtime.plan_progression", "First effect must be the declared first beat.")
	_ctx.equals(registry.calls[1]["effect_id"], &"line_b", &"runtime.plan_progression", "Progression must follow next_beat_id from dialogue_a to dialogue_b.")
	# Target resolves (contract 2) and is an adapter (contract 8).
	_ctx.equals(registry.calls[1]["context"]["target_actor"], villain, &"dialogue.target_resolves", "Non-empty target must resolve by target_actor_id.")
	_ctx.is_true(registry.calls[1]["context"]["target_actor"] is SceneActorAdapter, &"dialogue.target_is_adapter", "Target must be an actor adapter, not a scene node.")
	_ctx.equals(registry.calls[1]["context"]["scene_beat_id"], &"dialogue_b", &"dialogue.context_beat_id", "Second effect context must carry its own beat id.")

	# Complete dialogue_b; scene finishes exactly once, no failure.
	hero.finish_dialogue()
	var terminal: Dictionary = runtime["terminal"]
	_ctx.equals(terminal["finished"], 1, &"runtime.scene_finishes", "Scene must finish once after the last beat.")
	_ctx.equals(terminal["failed"], 0, &"runtime.scene_finishes", "No failure may occur on a valid plan.")

	await _teardown(runtime)


# --------------------------------------------------------------------------- #
# Contract 4, 14: missing speaker
# --------------------------------------------------------------------------- #

func _test_missing_speaker_fails() -> void:
	var runtime := _make_runtime()
	var plan := load(FIXTURE_MISSING_SPEAKER) as ScenePlan
	if not _ctx.is_true(plan != null, &"fixture.missing_speaker_loads", "invalid_missing_speaker_plan.tres must load"):
		await _teardown(runtime)
		return

	_start(runtime, plan)

	var terminal: Dictionary = runtime["terminal"]
	_ctx.equals(terminal["failed"], 1, &"dialogue.missing_speaker_fails", "Unbound speaker must emit one failure.")
	_ctx.equals(terminal["failed_reason"], &"scene_animator.missing_speaker_actor", &"dialogue.missing_speaker_fails", "Failure reason must be the stable dotted code.")
	# Diagnostics retain beat + actor IDs (contract 14).
	_ctx.equals(terminal["failed_details"].get("beat_id"), &"bad_speaker", &"runtime.diagnostics_retain_beat", "Failure details must retain the beat id.")
	_ctx.equals(terminal["failed_details"].get("speaker_actor_id"), &"ghost", &"dialogue.missing_speaker_fails", "Failure details must retain the speaker actor id.")
	_ctx.equals(terminal["failed_details"].get("target_actor_id"), &"", &"dialogue.missing_speaker_fails", "Failure details must retain the target actor id.")
	_ctx.equals((runtime["registry"] as FakeMechanicsRegistry).calls.size(), 0, &"dialogue.missing_speaker_fails", "No effect may play when the speaker is missing.")

	await _teardown(runtime)


# --------------------------------------------------------------------------- #
# Contract 5, 14: unknown target
# --------------------------------------------------------------------------- #

func _test_unknown_target_fails() -> void:
	var runtime := _make_runtime()
	var plan := load(FIXTURE_UNKNOWN_TARGET) as ScenePlan
	if not _ctx.is_true(plan != null, &"fixture.unknown_target_loads", "invalid_unknown_target_plan.tres must load"):
		await _teardown(runtime)
		return

	_start(runtime, plan)

	var terminal: Dictionary = runtime["terminal"]
	_ctx.equals(terminal["failed"], 1, &"dialogue.missing_target_fails", "Unbound non-empty target must emit one failure.")
	_ctx.equals(terminal["failed_reason"], &"scene_animator.missing_target_actor", &"dialogue.missing_target_fails", "Failure reason must be the stable dotted code.")
	_ctx.equals(terminal["failed_details"].get("beat_id"), &"bad_target", &"runtime.diagnostics_retain_beat", "Failure details must retain the beat id.")
	_ctx.equals(terminal["failed_details"].get("target_actor_id"), &"phantom", &"dialogue.missing_target_fails", "Failure details must retain the target actor id.")
	_ctx.equals(terminal["failed_details"].get("speaker_actor_id"), &"hero", &"dialogue.missing_target_fails", "Failure details must retain the speaker actor id.")
	_ctx.equals((runtime["registry"] as FakeMechanicsRegistry).calls.size(), 0, &"dialogue.missing_target_fails", "No effect may play when resolution fails.")

	await _teardown(runtime)


# --------------------------------------------------------------------------- #
# Contract 12: terminal failure blocks later beats
# --------------------------------------------------------------------------- #

func _test_terminal_failure_blocks_later_beats() -> void:
	var runtime := _make_runtime()
	var plan := ScenePlan.new()
	plan.plan_id = &"terminal_block"

	var bad := DialogueBeat.new()
	bad.beat_id = &"block_speaker"
	bad.speaker_actor_id = &"ghost_block"
	bad.dialogue_id = &"line_never"
	bad.next_beat_id = &"block_effect"
	var good := DialogueBeat.new()
	good.beat_id = &"block_effect"
	good.speaker_actor_id = &"hero"
	good.dialogue_id = &"line_should_not_play"
	plan.beats = [bad, good]

	var registry: FakeMechanicsRegistry = runtime["registry"]
	registry.register_effect(&"line_should_not_play", func(payload: Dictionary) -> void: pass)

	_start(runtime, plan)

	var terminal: Dictionary = runtime["terminal"]
	_ctx.equals(terminal["failed"], 1, &"runtime.terminal_failure_blocks_later", "A beat failure with no failure_beat_id must terminate the scene once.")
	_ctx.equals(terminal["failed_reason"], &"scene_animator.missing_speaker_actor", &"runtime.terminal_failure_blocks_later", "Terminal failure must carry the originating reason.")
	_ctx.equals(registry.calls.size(), 0, &"runtime.terminal_failure_blocks_later", "Later beats must not execute after a terminal failure.")

	await _teardown(runtime)


# --------------------------------------------------------------------------- #
# Contract 13: empty plan reaches a deterministic terminal outcome
# --------------------------------------------------------------------------- #

func _test_empty_plan_deterministic() -> void:
	var runtime := _make_runtime()
	var plan := ScenePlan.new()
	plan.plan_id = &"empty_plan"

	_start(runtime, plan)

	var terminal: Dictionary = runtime["terminal"]
	_ctx.equals(terminal["failed"], 1, &"runtime.empty_plan_deterministic", "An empty plan must reach exactly one terminal outcome.")
	_ctx.equals(terminal["finished"], 0, &"runtime.empty_plan_deterministic", "An empty plan must not emit scene_finished.")
	_ctx.equals(terminal["failed_reason"], &"empty_plan", &"runtime.empty_plan_deterministic", "Empty plan failure must carry the empty_plan reason.")
	_ctx.equals(terminal["failed_details"].get("plan_id"), &"empty_plan", &"runtime.empty_plan_deterministic", "Empty plan failure must retain the plan id.")
	_ctx.equals((runtime["registry"] as FakeMechanicsRegistry).calls.size(), 0, &"runtime.empty_plan_deterministic", "An empty plan must not invoke any effect.")

	await _teardown(runtime)
