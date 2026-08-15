class_name TestValidators
extends RefCounted

## Authoring-validation contract suite. Exercises every rule in the
## ScenePlanValidator against programmatic plans and the serialized fixtures.
## Errors block playback; warnings are tolerated; a plan is valid iff it has no
## errors.

const FIXTURE_VALID := "res://addons/scene_animator/tests/fixtures/valid_linear_scene_plan.tres"
const FIXTURE_DUPLICATE := "res://addons/scene_animator/tests/fixtures/invalid_duplicate_beat_ids_plan.tres"
const FIXTURE_DANGLING := "res://addons/scene_animator/tests/fixtures/invalid_dangling_next_plan.tres"

var _ctx: SceneAnimatorTestContext


func run() -> SceneAnimatorTestResult:
	var result := SceneAnimatorTestResult.new()
	result.suite_name = &"test_validators"
	_ctx = SceneAnimatorTestContext.new(result)
	var started_ms := Time.get_ticks_msec()

	_test_valid_fixture_is_valid()
	_test_null_plan()
	_test_empty_plan()
	_test_plan_meta_warnings()
	_test_actor_identity_issues()
	_test_beat_identity_issues()
	_test_fixture_duplicate_beat_ids()
	_test_fixture_dangling_next()
	_test_flow_issues()
	_test_reachability()
	_test_capability_issues()

	result.duration_ms = Time.get_ticks_msec() - started_ms
	return result


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #

## A runnable plan: one dialogue beat, no errors, several benign warnings.
func _base_plan() -> ScenePlan:
	var plan := ScenePlan.new()
	plan.plan_id = &"test_plan"
	var beat := DialogueBeat.new()
	beat.beat_id = &"a"
	beat.speaker_actor_id = &"hero"
	beat.dialogue_id = &"line_a"
	plan.beats = [beat]
	return plan


func _registry() -> SceneCapabilityRegistry:
	var reg := SceneCapabilityRegistry.new()
	var action := ActionDefinition.new()
	action.id = &"punch"
	action.required_actor_tags = [&"combat"]
	reg.actions = [action]
	var cam := CameraModeDefinition.new()
	cam.id = &"closeup"
	cam.requires_focus_target = true
	reg.camera_modes = [cam]
	var enc := EncounterDefinition.new()
	enc.id = &"wolf_pack"
	reg.encounters = [enc]
	var cond := ConditionDefinition.new()
	cond.id = &"is_day"
	reg.conditions = [cond]
	return reg


func _has(result: ScenePlanValidationResult, code: StringName) -> bool:
	return result.issue_codes().has(code)


# --------------------------------------------------------------------------- #
# Cases
# --------------------------------------------------------------------------- #

func _test_valid_fixture_is_valid() -> void:
	var plan := load(FIXTURE_VALID) as ScenePlan
	if not _ctx.is_true(plan != null, &"validator.fixture_valid_loads", "valid_linear_scene_plan.tres must load."):
		return
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(result.is_valid(), &"validator.valid_fixture_playable", "The runtime-valid fixture must be validator-valid (no errors).")
	_ctx.is_true(not _has(result, &"scene_animator.validation.dangling_next"), &"validator.valid_fixture_no_dangling", "Valid fixture must not report dangling flow.")


func _test_null_plan() -> void:
	var result := ScenePlanValidator.validate(null)
	_ctx.is_true(_has(result, &"scene_animator.validation.null_plan"), &"validator.null_plan", "Null plan must report null_plan.")
	_ctx.is_true(not result.is_valid(), &"validator.null_plan_invalid", "Null plan must be invalid.")


func _test_empty_plan() -> void:
	var plan := ScenePlan.new()
	plan.plan_id = &"empty"
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.empty_plan"), &"validator.empty_plan", "Plan with no beats must report empty_plan.")
	_ctx.is_true(not result.is_valid(), &"validator.empty_plan_invalid", "Empty plan must be invalid.")


func _test_plan_meta_warnings() -> void:
	var plan := _base_plan()
	plan.plan_id = &""
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.plan_id_missing"), &"validator.plan_id_missing", "Plan without plan_id must warn.")
	_ctx.is_true(_has(result, &"scene_animator.validation.no_actors"), &"validator.no_actors", "Plan without actors must warn.")
	_ctx.is_true(_has(result, &"scene_animator.validation.no_capability_registry"), &"validator.no_registry_warn", "Missing capability registry must warn and skip capability checks.")
	_ctx.is_true(result.is_valid(), &"validator.meta_warnings_tolerated", "Metadata warnings must not block playback.")


func _test_actor_identity_issues() -> void:
	var plan := _base_plan()
	var duplicate := SceneActorBinding.new()
	duplicate.actor_id = &"hero"
	var unnamed := SceneActorBinding.new()
	plan.actors = [duplicate, duplicate, unnamed]
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.duplicate_actor_id"), &"validator.duplicate_actor", "Duplicate actor ids must error.")
	_ctx.is_true(_has(result, &"scene_animator.validation.actor_id_missing"), &"validator.actor_id_missing", "Actor binding without actor_id must error.")
	_ctx.is_true(not result.is_valid(), &"validator.actor_errors_block", "Actor identity errors must block playback.")


func _test_beat_identity_issues() -> void:
	var plan := _base_plan()
	var unnamed := DialogueBeat.new()
	unnamed.speaker_actor_id = &"hero"
	plan.beats.append(unnamed)
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.beat_id_missing"), &"validator.beat_id_missing", "Beat without beat_id must error.")


func _test_fixture_duplicate_beat_ids() -> void:
	var plan := load(FIXTURE_DUPLICATE) as ScenePlan
	if not _ctx.is_true(plan != null, &"validator.fixture_duplicate_loads", "invalid_duplicate_beat_ids_plan.tres must load."):
		return
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.duplicate_beat_id"), &"validator.duplicate_beat", "Duplicate beat ids must error.")
	_ctx.is_true(not result.is_valid(), &"validator.duplicate_beat_invalid", "Duplicate beat ids must block playback.")


func _test_fixture_dangling_next() -> void:
	var plan := load(FIXTURE_DANGLING) as ScenePlan
	if not _ctx.is_true(plan != null, &"validator.fixture_dangling_loads", "invalid_dangling_next_plan.tres must load."):
		return
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.dangling_next"), &"validator.dangling_next", "next_beat_id to a missing beat must error.")
	_ctx.is_true(not result.is_valid(), &"validator.dangling_next_invalid", "Dangling next must block playback.")


func _test_flow_issues() -> void:
	var plan := _base_plan()
	var flow := DialogueBeat.new()
	flow.beat_id = &"flow"
	flow.speaker_actor_id = &"hero"
	flow.next_beat_id = &"missing_next"
	flow.failure_beat_id = &"missing_failure"
	plan.beats.append(flow)

	var branch := BranchBeat.new()
	branch.beat_id = &"branch"
	branch.target_beat_id = &"missing_branch"
	plan.beats.append(branch)

	var self_branch := BranchBeat.new()
	self_branch.beat_id = &"self_branch"
	self_branch.target_beat_id = &"self_branch"
	plan.beats.append(self_branch)

	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.dangling_next"), &"validator.dangling_next_flow", "Dangling next_beat_id must error.")
	_ctx.is_true(_has(result, &"scene_animator.validation.dangling_failure"), &"validator.dangling_failure", "Dangling failure_beat_id must error.")
	_ctx.is_true(_has(result, &"scene_animator.validation.dangling_branch_target"), &"validator.dangling_branch", "Dangling branch target must error.")
	_ctx.is_true(_has(result, &"scene_animator.validation.branch_self_target"), &"validator.branch_self", "Branch targeting itself must warn.")
	_ctx.is_true(not result.is_valid(), &"validator.flow_errors_block", "Flow errors must block playback.")


func _test_reachability() -> void:
	var plan := _base_plan()
	var reachable := DialogueBeat.new()
	reachable.beat_id = &"b"
	reachable.speaker_actor_id = &"hero"
	reachable.next_beat_id = &"a"
	plan.beats.append(reachable)
	var orphan := DialogueBeat.new()
	orphan.beat_id = &"orphan"
	orphan.speaker_actor_id = &"hero"
	plan.beats.append(orphan)
	var result := ScenePlanValidator.validate(plan)
	_ctx.is_true(_has(result, &"scene_animator.validation.unreachable_beat"), &"validator.unreachable", "Enabled beat not reachable from the start must warn.")

	var disabled_only := ScenePlan.new()
	disabled_only.plan_id = &"all_disabled"
	var off := DialogueBeat.new()
	off.beat_id = &"off"
	off.speaker_actor_id = &"hero"
	off.enabled = false
	disabled_only.beats = [off]
	var disabled_result := ScenePlanValidator.validate(disabled_only)
	_ctx.is_true(_has(disabled_result, &"scene_animator.validation.no_enabled_beats"), &"validator.no_enabled", "Plan with no enabled beats must error.")
	_ctx.is_true(not disabled_result.is_valid(), &"validator.no_enabled_invalid", "No enabled beats must block playback.")


func _test_capability_issues() -> void:
	var reg := _registry()
	var plan := _base_plan()

	var action_bad := ActionBeat.new()
	action_bad.beat_id = &"action_bad"
	action_bad.actor_id = &"hero"
	action_bad.action_id = &"nonexistent_action"
	plan.beats.append(action_bad)

	var action_tags := ActionBeat.new()
	action_tags.beat_id = &"action_tags"
	action_tags.actor_id = &"hero"
	action_tags.action_id = &"punch"
	plan.beats.append(action_tags)

	var camera_bad := CameraBeat.new()
	camera_bad.beat_id = &"camera_bad"
	camera_bad.camera_mode_id = &"nonexistent_mode"
	plan.beats.append(camera_bad)

	var camera_focus := CameraBeat.new()
	camera_focus.beat_id = &"camera_focus"
	camera_focus.camera_mode_id = &"closeup"
	plan.beats.append(camera_focus)

	var encounter_bad := SpawnEncounterBeat.new()
	encounter_bad.beat_id = &"encounter_bad"
	encounter_bad.encounter_id = &"nonexistent_encounter"
	plan.beats.append(encounter_bad)

	var branch_bad := BranchBeat.new()
	branch_bad.beat_id = &"branch_bad"
	branch_bad.condition_id = &"nonexistent_condition"
	plan.beats.append(branch_bad)

	var result := ScenePlanValidator.validate(plan, reg)
	_ctx.is_true(_has(result, &"scene_animator.validation.unknown_action"), &"validator.unknown_action", "Unregistered action must error.")
	_ctx.is_true(_has(result, &"scene_animator.validation.action_tag_mismatch"), &"validator.action_tags", "Actor tags failing an action's requirements must warn.")
	_ctx.is_true(_has(result, &"scene_animator.validation.unknown_camera_mode"), &"validator.unknown_camera", "Unregistered camera mode must error.")
	_ctx.is_true(_has(result, &"scene_animator.validation.missing_focus"), &"validator.missing_focus", "Focus-requiring camera without focus target must warn.")
	_ctx.is_true(_has(result, &"scene_animator.validation.unknown_encounter"), &"validator.unknown_encounter", "Unregistered encounter must error.")
	_ctx.is_true(_has(result, &"scene_animator.validation.unknown_condition"), &"validator.unknown_condition", "Unregistered condition must error.")
	_ctx.is_true(not result.is_valid(), &"validator.capability_errors_block", "Capability errors must block playback.")
