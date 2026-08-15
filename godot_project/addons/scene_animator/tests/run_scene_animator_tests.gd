@tool
extends SceneTree

## Master headless test runner. Loads each suite in fixed order, catches
## suite-load / fixture-load failures as infrastructure errors, aggregates
## results, and prints exactly one terminal machine-readable JSON line.
##
## Run:
##   godot --headless --path godot_project \
##     --script res://addons/scene_animator/tests/run_scene_animator_tests.gd
##
## Exit codes: 0 all pass, 1 assertion/contract failure, 2 infrastructure
## failure.

const SUITE_PATHS: Array[String] = [
	"res://addons/scene_animator/tests/test_runtime_execution.gd",
	"res://addons/scene_animator/tests/test_plugin_activation.gd",
	"res://addons/scene_animator/tests/test_validators.gd",
]

const RESULT_PREFIX := "SCENE_ANIMATOR_RESULT: "


func _init() -> void:
	call_deferred("_run_all")


func _run_all() -> void:
	var started_ms := Time.get_ticks_msec()
	var infra_failed := false
	var infra_errors: Array[String] = []
	var suites_total := SUITE_PATHS.size()
	var suites_passed := 0
	var total_assertions := 0
	var total_failures: Array[Dictionary] = []
	var failure_ids: Array[StringName] = []

	var suite: RefCounted = null
	for path in SUITE_PATHS:
		var suite_script = load(path)
		if suite_script == null:
			infra_failed = true
			infra_errors.append("suite load failed: " + path)
			continue
		suite = suite_script.new()
		if suite == null or not (suite is RefCounted):
			infra_failed = true
			infra_errors.append("suite instantiation failed: " + path)
			continue
		var result: SceneAnimatorTestResult = await suite.run()
		if result == null:
			infra_failed = true
			infra_errors.append("suite returned no result: " + path)
			continue
		total_assertions += result.assertions
		if result.passed:
			suites_passed += 1
		else:
			for failure in result.failures:
				failure_ids.append(failure["id"])
				total_failures.append({
					"suite": result.suite_name,
					"id": failure["id"],
					"message": failure["message"],
				})
		suite = null
		suite_script = null
		await process_frame

	var duration_ms := Time.get_ticks_msec() - started_ms

	var status := "PASS"
	var exit_code := 0
	if infra_failed:
		status = "ERROR"
		exit_code = 2
	elif not total_failures.is_empty():
		status = "FAIL"
		exit_code = 1

	var report_suite := "runtime"
	if not total_failures.is_empty():
		report_suite = str(total_failures[0]["suite"])
	elif infra_failed:
		report_suite = "runner"

	var version := Engine.get_version_info()
	var report: Dictionary = {
		"schema_version": 1,
		"status": status,
		"suite": report_suite,
		"suites_total": suites_total,
		"suites_passed": suites_passed,
		"assertions": total_assertions,
		"failures": total_failures.size(),
		"duration_ms": duration_ms,
		"godot_version": "%d.%d.%d" % [version["major"], version["minor"], version["patch"]],
		"mode": "headless",
	}
	if infra_failed:
		report["infra_errors"] = infra_errors
	if not total_failures.is_empty():
		report["failure_ids"] = failure_ids

	for e in infra_errors:
		print("INFRA_ERROR: ", e)
	for f in total_failures:
		print("TEST_FAIL: suite=%s id=%s message=%s" % [f["suite"], f["id"], f["message"]])
	print(RESULT_PREFIX + JSON.stringify(report))
	quit(exit_code)
