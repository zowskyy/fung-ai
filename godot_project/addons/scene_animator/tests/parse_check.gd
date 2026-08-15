@tool
extends SceneTree

## Loads every addon .gd and test resource in strict dependency order and reports
## any load failure (syntax error or unresolved class-name type hint). Each
## runner is its own process, so this script re-establishes the full graph.
##
## Run:
##   godot --headless --path godot_project \
##     --script res://addons/scene_animator/tests/parse_check.gd

const ADDON := "res://addons/scene_animator/"

const DIALOGUE_RUNNER_PATH := (
	"res://addons/scene_animator/runtime/runners/dialogue_beat_runner.gd"
)

# Dependency order: a script only references classes defined earlier in the
# list (or engine classes), so a raw load() resolves every type hint.
# Runtime loads inside factory functions (load(), not preload) are deferred to
# execution time and are covered by the behavior runners.
var _order: Array[String] = [
	# data definitions (no addon deps)
	"data/action_definition.gd",
	"data/interaction_definition.gd",
	"data/camera_mode_definition.gd",
	"data/encounter_definition.gd",
	"data/condition_definition.gd",
	# data containers (ref definitions)
	"data/scene_capability_registry.gd",
	"data/scene_actor_binding.gd",
	"data/scene_beat.gd",
	"data/scene_plan.gd",
	# beat subtypes (ref SceneBeat)
	"data/beats/move_to_beat.gd",
	"data/beats/look_at_beat.gd",
	"data/beats/action_beat.gd",
	"data/beats/wait_beat.gd",
	"data/beats/wait_for_event_beat.gd",
	"data/beats/camera_beat.gd",
	"data/beats/dialogue_beat.gd",
	"data/beats/set_state_beat.gd",
	"data/beats/spawn_encounter_beat.gd",
	"data/beats/branch_beat.gd",
	"data/beats/end_beat.gd",
	# runtime bases
	"runtime/scene_actor_adapter.gd",
	"runtime/scene_camera_adapter.gd",
	# runtime containers (ref actor + camera types)
	"runtime/scene_mechanics_registry.gd",
	"runtime/scene_bindings.gd",
	"runtime/beat_runner.gd",
	"runtime/placeholder_actor_adapter.gd",
	# runtime runners (ref BeatRunner + beat types)
	"runtime/runners/move_to_beat_runner.gd",
	"runtime/runners/look_at_beat_runner.gd",
	"runtime/runners/action_beat_runner.gd",
	"runtime/runners/wait_beat_runner.gd",
	"runtime/runners/wait_for_event_beat_runner.gd",
	"runtime/runners/camera_beat_runner.gd",
	"runtime/runners/dialogue_beat_runner.gd",
	"runtime/runners/set_state_beat_runner.gd",
	"runtime/runners/spawn_encounter_beat_runner.gd",
	"runtime/runners/branch_beat_runner.gd",
	"runtime/runners/end_beat_runner.gd",
	# director (refs plan/bindings/registry/beat runner types)
	"runtime/scene_director.gd",
	# runnable demo (refs director/bindings/registry/placeholder actors/plan)
	"demo/demo_scene.gd",
	# editor validation core (pure RefCounted, no editor deps)
	"editor/validators/validation_issue.gd",
	"editor/validators/scene_plan_validation_result.gd",
	"editor/validators/scene_plan_validator.gd",
	# editor UI (ref validator + engine editor classes)
	"editor/scene_plan_dock.gd",
	"editor/inspectors/scene_plan_inspector.gd",
	# editor plugin (ref dock + inspector)
	"plugin.gd",
	# test harness (ref runtime types + each other)
	"tests/support/test_result.gd",
	"tests/support/test_context.gd",
	"tests/support/fake_actor_adapter.gd",
	"tests/support/fake_camera_adapter.gd",
	"tests/support/fake_mechanics_registry.gd",
	"tests/test_runtime_execution.gd",
	"tests/test_plugin_activation.gd",
	"tests/test_validators.gd",
	"tests/test_demo_execution.gd",
	"tests/run_scene_animator_tests.gd",
	"tests/parse_check.gd",
]

var _resources: Array[String] = [
	"templates/starter_scene_plan.tres",
	"demo/demo_scene_plan.tres",
	"demo/demo_scene.tscn",
	"tests/fixtures/valid_linear_scene_plan.tres",
	"tests/fixtures/invalid_missing_speaker_plan.tres",
	"tests/fixtures/invalid_unknown_target_plan.tres",
	"tests/fixtures/invalid_duplicate_beat_ids_plan.tres",
	"tests/fixtures/invalid_dangling_next_plan.tres",
]

var _ok := true
var _errors: Array[String] = []


func _init() -> void:
	for rel: String in _order:
		var path: String = ADDON + rel
		var script = load(path)
		if script == null:
			_ok = false
			_errors.append("load failed: " + path)

	for rel: String in _resources:
		var path: String = ADDON + rel
		if not FileAccess.file_exists(path):
			continue
		var res = load(path)
		if res == null:
			_ok = false
			_errors.append("resource load failed: " + path)

	# Force instantiation of representative core types to surface any remaining
	# unresolved references that load() defers.
	if _ok:
		_smoke_instantiate()

	_ok = _assert_no_legacy_target_path() and _ok
	_ok = _assert_manifest_covers_tree() and _ok

	_print()


func _smoke_instantiate() -> void:
	var Director := load(ADDON + "runtime/scene_director.gd")
	var Registry := load(ADDON + "data/scene_capability_registry.gd")
	var Plan := load(ADDON + "data/scene_plan.gd")
	if Director == null or Registry == null or Plan == null:
		_ok = false
		_errors.append("smoke: core script missing")
		return
	var director = Director.new()
	if not (director.get_script() == Director):
		_ok = false
		_errors.append("smoke: director script mismatch")
	director.queue_free()
	var registry = Registry.new()
	if not (registry.get_script() == Registry):
		_ok = false
		_errors.append("smoke: registry script mismatch")
	registry = null
	var plan = Plan.new()
	if not (plan.get_script() == Plan):
		_ok = false
		_errors.append("smoke: plan script mismatch")
	plan = null


func _assert_no_legacy_target_path() -> bool:
	var file := FileAccess.open(DIALOGUE_RUNNER_PATH, FileAccess.READ)
	if file == null:
		push_error(
			"Phase 0 guard could not open dialogue runner: %s"
			% DIALOGUE_RUNNER_PATH
		)
		return false

	var source := file.get_as_text()
	if source.contains(".target_path"):
		push_error(
			"Legacy DialogueBeat access remains in dialogue_beat_runner.gd: "
			+ "use target_actor_id via SceneBindings."
		)
		return false

	return true


func _walk_gd(rel_dir: String, found: Array[String]) -> void:
	for child in DirAccess.get_directories_at(ADDON + rel_dir):
		_walk_gd(rel_dir + child + "/", found)
	for file in DirAccess.get_files_at(ADDON + rel_dir):
		if file.ends_with(".gd"):
			found.append(rel_dir + file)


func _assert_manifest_covers_tree() -> bool:
	var ok := true
	var found: Array[String] = []
	_walk_gd("", found)
	for rel in found:
		if not _order.has(rel):
			ok = false
			_errors.append("script missing from manifest: " + rel)
	return ok


func _print() -> void:
	var total := _order.size() + _resources.size()
	for e: String in _errors:
		print("PARSE_ERROR: ", e)
	print("Parsed %d scripts." % total)
	if _ok:
		print("PARSE_CHECK: PASS")
	else:
		print("PARSE_CHECK: FAIL")
	quit(0 if _ok else 1)
