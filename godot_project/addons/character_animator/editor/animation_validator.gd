@tool
class_name AnimationValidator
extends RefCounted
## Validates a character setup (profile + scene target) and returns a list of
## structured ValidationIssue results the dock can display and act on.

static func validate(target: Node, profile: CharacterAnimationProfile) -> Array[ValidationIssue]:
	var issues: Array[ValidationIssue] = []
	if target == null or profile == null:
		issues.append(ValidationIssue.make(
			ValidationIssue.Severity.ERROR, "No target node or profile provided."))
		return issues

	var animator := _resolve_animator(target, profile)
	if profile.animator_path != NodePath() and animator == null:
		issues.append(ValidationIssue.make(
			ValidationIssue.Severity.ERROR,
			"Profile animator_path does not resolve to a Sprite2D.",
			profile.animator_path))

	var player := _resolve_player(target, profile)

	for required in profile.required_animation_names():
		if required == &"":
			continue
		if not _has_clip(animator, player, required):
			issues.append(ValidationIssue.make(
				ValidationIssue.Severity.ERROR,
				"Required clip '%s' is missing from the source and the AnimationPlayer." % required))

	for optional in [profile.walk, profile.land, profile.crouch_idle, profile.crouch_move, profile.attack_1, profile.hurt]:
		if optional == &"":
			continue
		if not _has_clip(animator, player, optional):
			issues.append(ValidationIssue.make(
				ValidationIssue.Severity.WARNING,
				"Optional clip '%s' was not found; the generated graph will skip it." % optional))

	if profile.visuals_path != NodePath() and target.get_node_or_null(profile.visuals_path) == null:
		issues.append(ValidationIssue.make(
			ValidationIssue.Severity.WARNING,
			"Visuals path does not resolve; facing flips will not apply.",
			profile.visuals_path))

	var tree := target.get_node_or_null("AnimationTree") as AnimationTree
	if tree != null:
		var tree_player := tree.get_node_or_null(tree.anim_player) as AnimationPlayer
		if tree.anim_player == NodePath() or tree_player == null:
			issues.append(ValidationIssue.make(
				ValidationIssue.Severity.ERROR,
				"AnimationTree has no AnimationPlayer assigned."))
		elif player != null and tree_player != player:
			issues.append(ValidationIssue.make(
				ValidationIssue.Severity.WARNING,
				"AnimationTree's AnimationPlayer differs from the profile's."))
	else:
		issues.append(ValidationIssue.make(
			ValidationIssue.Severity.WARNING,
			"No AnimationTree found. Run Generate in the Setup tab."))

	if profile.walk_point >= profile.run_point:
		issues.append(ValidationIssue.make(
			ValidationIssue.Severity.WARNING,
			"walk_point should be lower than run_point for a sane blend space."))

	return issues


static func _resolve_animator(target: Node, profile: CharacterAnimationProfile) -> Sprite2D:
	if profile.animator_path != NodePath():
		var node := target.get_node_or_null(profile.animator_path)
		if node is Sprite2D:
			return node
	for child in target.get_children():
		if child is CharacterAnimator:
			return child
	return null


static func _resolve_player(target: Node, profile: CharacterAnimationProfile) -> AnimationPlayer:
	if profile.animation_player_path != NodePath():
		var node := target.get_node_or_null(profile.animation_player_path)
		if node is AnimationPlayer:
			return node
	return target.get_node_or_null("AnimationPlayer") as AnimationPlayer


static func _has_clip(animator: Sprite2D, player: AnimationPlayer, clip_name: StringName) -> bool:
	if animator != null and animator.has_method("has_animation") and animator.has_animation(clip_name):
		return true
	if player != null and player.has_animation(String(clip_name)):
		return true
	return false
