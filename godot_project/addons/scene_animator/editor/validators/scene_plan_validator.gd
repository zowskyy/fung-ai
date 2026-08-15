@tool
class_name ScenePlanValidator
extends RefCounted

## Authoring-time validation for ScenePlan resources. Pure and dependency-free
## (it only reads the plan and the optional capability registry), so it runs in
## the headless test runner, the editor dock, and the inspector alike.
##
## Contract: a plan is "valid" when it has no ERROR issues. Warnings flag
## suspicious-but-runnable authoring. Issue codes are stable under the
## scene_animator.validation.* namespace and mirror the runtime failure codes
## where a beat would fail at play time.

const CODE_NULL_PLAN := &"scene_animator.validation.null_plan"
const CODE_PLAN_ID_MISSING := &"scene_animator.validation.plan_id_missing"
const CODE_EMPTY_PLAN := &"scene_animator.validation.empty_plan"
const CODE_NO_ACTORS := &"scene_animator.validation.no_actors"
const CODE_ACTOR_ID_MISSING := &"scene_animator.validation.actor_id_missing"
const CODE_DUPLICATE_ACTOR_ID := &"scene_animator.validation.duplicate_actor_id"
const CODE_BEAT_ID_MISSING := &"scene_animator.validation.beat_id_missing"
const CODE_DUPLICATE_BEAT_ID := &"scene_animator.validation.duplicate_beat_id"
const CODE_NO_ENABLED_BEATS := &"scene_animator.validation.no_enabled_beats"
const CODE_DANGLING_NEXT := &"scene_animator.validation.dangling_next"
const CODE_DANGLING_FAILURE := &"scene_animator.validation.dangling_failure"
const CODE_DANGLING_BRANCH_TARGET := &"scene_animator.validation.dangling_branch_target"
const CODE_BRANCH_SELF_TARGET := &"scene_animator.validation.branch_self_target"
const CODE_UNREACHABLE_BEAT := &"scene_animator.validation.unreachable_beat"
const CODE_MISSING_SPEAKER := &"scene_animator.validation.missing_speaker"
const CODE_MISSING_ACTOR := &"scene_animator.validation.missing_actor"
const CODE_UNKNOWN_ACTOR := &"scene_animator.validation.unknown_actor"
const CODE_NO_CAPABILITY_REGISTRY := &"scene_animator.validation.no_capability_registry"
const CODE_UNKNOWN_ACTION := &"scene_animator.validation.unknown_action"
const CODE_ACTION_TAG_MISMATCH := &"scene_animator.validation.action_tag_mismatch"
const CODE_UNKNOWN_CAMERA_MODE := &"scene_animator.validation.unknown_camera_mode"
const CODE_MISSING_FOCUS := &"scene_animator.validation.missing_focus"
const CODE_UNKNOWN_ENCOUNTER := &"scene_animator.validation.unknown_encounter"
const CODE_UNKNOWN_CONDITION := &"scene_animator.validation.unknown_condition"


static func validate(plan: ScenePlan, registry: SceneCapabilityRegistry = null) -> ScenePlanValidationResult:
	var result := ScenePlanValidationResult.new()
	if plan == null:
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.ERROR,
			CODE_NULL_PLAN,
			"Plan is null."
		))
		return result
	result.plan_id = plan.plan_id
	_validate_plan_meta(plan, result)
	_validate_actors(plan, result)
	_validate_beats(plan, result)
	_validate_reachability(plan, result)
	if registry == null:
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.WARNING,
			CODE_NO_CAPABILITY_REGISTRY,
			"No capability registry provided; action/camera/encounter/condition checks were skipped."
		))
	else:
		_validate_capabilities(plan, registry, result)
	return result


static func _validate_plan_meta(plan: ScenePlan, result: ScenePlanValidationResult) -> void:
	if plan.plan_id == &"":
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.WARNING,
			CODE_PLAN_ID_MISSING,
			"Plan declares no plan_id."
		))
	if plan.beats.is_empty():
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.ERROR,
			CODE_EMPTY_PLAN,
			"Plan declares no beats and can never run."
		))
		return
	if plan.first_enabled_beat() == null:
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.ERROR,
			CODE_NO_ENABLED_BEATS,
			"Every beat is disabled; the plan can never start."
		))
	if plan.actors.is_empty():
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.WARNING,
			CODE_NO_ACTORS,
			"Plan declares no actors; actor-referencing beats will fail at runtime."
		))


static func _validate_actors(plan: ScenePlan, result: ScenePlanValidationResult) -> void:
	var seen: Dictionary = {}
	for actor: SceneActorBinding in plan.actors:
		if actor == null:
			continue
		if actor.actor_id == &"":
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_ACTOR_ID_MISSING,
				"An actor binding declares no actor_id.",
				&"",
				&""
			))
			continue
		if seen.has(actor.actor_id):
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_DUPLICATE_ACTOR_ID,
				"Actor id is declared more than once.",
				&"",
				actor.actor_id
			))
			continue
		seen[actor.actor_id] = true


static func _validate_beats(plan: ScenePlan, result: ScenePlanValidationResult) -> void:
	var seen: Dictionary = {}
	var actor_ids := _actor_ids(plan)
	for beat: SceneBeat in plan.beats:
		if beat == null:
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_BEAT_ID_MISSING,
				"Plan contains a null beat.",
				&""
			))
			continue
		if beat.beat_id == &"":
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_BEAT_ID_MISSING,
				"Beat declares no beat_id.",
				&""
			))
			continue
		if seen.has(beat.beat_id):
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_DUPLICATE_BEAT_ID,
				"Beat id is declared more than once.",
				beat.beat_id
			))
			continue
		seen[beat.beat_id] = true

		_check_flow(plan, beat, result)
		_check_actor_refs(plan, beat, actor_ids, result)


static func _check_flow(plan: ScenePlan, beat: SceneBeat, result: ScenePlanValidationResult) -> void:
	var known := _beat_ids(plan)
	if beat.next_beat_id != &"" and not known.has(beat.next_beat_id):
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.ERROR,
			CODE_DANGLING_NEXT,
			"next_beat_id references a beat that does not exist.",
			beat.beat_id
		))
	if beat.failure_beat_id != &"" and not known.has(beat.failure_beat_id):
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.ERROR,
			CODE_DANGLING_FAILURE,
			"failure_beat_id references a beat that does not exist.",
			beat.beat_id
		))
	if beat is BranchBeat:
		var branch := beat as BranchBeat
		for target: StringName in [branch.target_beat_id, branch.else_target_beat_id]:
			if target != &"" and not known.has(target):
				result.issues.append(ScenePlanValidationIssue.new(
					ScenePlanValidationIssue.Severity.ERROR,
					CODE_DANGLING_BRANCH_TARGET,
					"Branch target references a beat that does not exist.",
					beat.beat_id
				))
		if branch.target_beat_id == beat.beat_id or branch.else_target_beat_id == beat.beat_id:
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.WARNING,
				CODE_BRANCH_SELF_TARGET,
				"Branch targets itself; this loops forever unless a condition gates it.",
				beat.beat_id
			))


static func _check_actor_refs(plan: ScenePlan, beat: SceneBeat, actor_ids: Dictionary, result: ScenePlanValidationResult) -> void:
	if beat is DialogueBeat:
		var dialogue := beat as DialogueBeat
		if dialogue.speaker_actor_id == &"":
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_MISSING_SPEAKER,
				"Dialogue beat declares no speaker; the runner fails with missing_speaker_actor.",
				beat.beat_id
			))
		else:
			_check_actor_id(beat, dialogue.speaker_actor_id, actor_ids, result)
		_check_actor_id(beat, dialogue.target_actor_id, actor_ids, result, true)
	elif beat is ActionBeat:
		var action := beat as ActionBeat
		if action.actor_id == &"":
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_MISSING_ACTOR,
				"Action beat declares no actor.",
				beat.beat_id
			))
		else:
			_check_actor_id(beat, action.actor_id, actor_ids, result)
	elif beat is MoveToBeat:
		_check_actor_id(beat, (beat as MoveToBeat).actor_id, actor_ids, result)
	elif beat is LookAtBeat:
		_check_actor_id(beat, (beat as LookAtBeat).actor_id, actor_ids, result)
	elif beat is WaitForEventBeat:
		_check_actor_id(beat, (beat as WaitForEventBeat).source_actor_id, actor_ids, result)


static func _check_actor_id(
	beat: SceneBeat,
	actor_id: StringName,
	actor_ids: Dictionary,
	result: ScenePlanValidationResult,
	allow_empty := false
) -> void:
	if actor_id == &"":
		if not allow_empty:
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.ERROR,
				CODE_MISSING_ACTOR,
				"Beat references no actor id.",
				beat.beat_id
			))
		return
	if not actor_ids.has(actor_id):
		result.issues.append(ScenePlanValidationIssue.new(
			ScenePlanValidationIssue.Severity.ERROR,
			CODE_UNKNOWN_ACTOR,
			"Beat references an actor that is not declared in the plan.",
			beat.beat_id,
			actor_id
		))


static func _validate_reachability(plan: ScenePlan, result: ScenePlanValidationResult) -> void:
	var start := plan.first_enabled_beat()
	if start == null:
		return
	var reachable: Dictionary = {}
	var queue: Array[SceneBeat] = [start]
	reachable[start.beat_id] = true
	while not queue.is_empty():
		var beat: SceneBeat = queue.pop_back()
		var edges: Array[StringName] = [beat.next_beat_id, beat.failure_beat_id]
		if beat is BranchBeat:
			var branch := beat as BranchBeat
			edges.append(branch.target_beat_id)
			edges.append(branch.else_target_beat_id)
		for edge: StringName in edges:
			if edge == &"" or reachable.has(edge):
				continue
			var target := plan.beat_by_id(edge)
			if target == null:
				continue
			reachable[edge] = true
			queue.append(target)
	for beat: SceneBeat in plan.beats:
		if beat == null:
			continue
		if beat.enabled and not reachable.has(beat.beat_id):
			result.issues.append(ScenePlanValidationIssue.new(
				ScenePlanValidationIssue.Severity.WARNING,
				CODE_UNREACHABLE_BEAT,
				"Enabled beat is not reachable from the first enabled beat.",
				beat.beat_id
			))


static func _validate_capabilities(plan: ScenePlan, registry: SceneCapabilityRegistry, result: ScenePlanValidationResult) -> void:
	var actor_tags := _actor_tags(plan)
	for beat: SceneBeat in plan.beats:
		if beat == null:
			continue
		if beat is ActionBeat:
			var action := beat as ActionBeat
			if not registry.find_action(action.action_id):
				result.issues.append(ScenePlanValidationIssue.new(
					ScenePlanValidationIssue.Severity.ERROR,
					CODE_UNKNOWN_ACTION,
					"action_id is not registered in the capability registry.",
					beat.beat_id
				))
			else:
				var action_def := registry.find_action(action.action_id)
				var tags: Array[StringName] = actor_tags.get(action.actor_id, [])
				if not action_def.matches_tags(tags, []):
					result.issues.append(ScenePlanValidationIssue.new(
						ScenePlanValidationIssue.Severity.WARNING,
						CODE_ACTION_TAG_MISMATCH,
						"Actor tags do not satisfy the action's required actor tags.",
						beat.beat_id,
						action.actor_id
					))
		elif beat is CameraBeat:
			var camera := beat as CameraBeat
			var camera_def := registry.find_camera_mode(camera.camera_mode_id)
			if camera_def == null:
				result.issues.append(ScenePlanValidationIssue.new(
					ScenePlanValidationIssue.Severity.ERROR,
					CODE_UNKNOWN_CAMERA_MODE,
					"camera_mode_id is not registered in the capability registry.",
					beat.beat_id
				))
			elif camera_def.requires_focus_target and camera.focus_target_path.is_empty():
				result.issues.append(ScenePlanValidationIssue.new(
					ScenePlanValidationIssue.Severity.WARNING,
					CODE_MISSING_FOCUS,
					"Camera mode requires a focus target but focus_target_path is empty.",
					beat.beat_id
				))
		elif beat is SpawnEncounterBeat:
			if not registry.find_encounter((beat as SpawnEncounterBeat).encounter_id):
				result.issues.append(ScenePlanValidationIssue.new(
					ScenePlanValidationIssue.Severity.ERROR,
					CODE_UNKNOWN_ENCOUNTER,
					"encounter_id is not registered in the capability registry.",
					beat.beat_id
				))
		elif beat is BranchBeat:
			var branch := beat as BranchBeat
			if branch.condition_id != &"" and not registry.find_condition(branch.condition_id):
				result.issues.append(ScenePlanValidationIssue.new(
					ScenePlanValidationIssue.Severity.ERROR,
					CODE_UNKNOWN_CONDITION,
					"condition_id is not registered in the capability registry.",
					beat.beat_id
				))


static func _actor_ids(plan: ScenePlan) -> Dictionary:
	var ids: Dictionary = {}
	for actor: SceneActorBinding in plan.actors:
		if actor != null and actor.actor_id != &"":
			ids[actor.actor_id] = true
	return ids


static func _beat_ids(plan: ScenePlan) -> Dictionary:
	var ids: Dictionary = {}
	for beat: SceneBeat in plan.beats:
		if beat != null and beat.beat_id != &"":
			ids[beat.beat_id] = true
	return ids


static func _actor_tags(plan: ScenePlan) -> Dictionary:
	var tags: Dictionary = {}
	for actor: SceneActorBinding in plan.actors:
		if actor != null and actor.actor_id != &"":
			tags[actor.actor_id] = actor.actor_tags
	return tags
