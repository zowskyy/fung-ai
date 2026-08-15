@tool
class_name AnimationGraphBuilder
extends RefCounted
## Generates (and later regenerates) an AnimationPlayer + AnimationTree graph
## from a CharacterAnimationProfile, converting CharacterAnimator frame clips
## into real Animation resources when available.
##
## Ownership model: every node/Animation this builder creates is tagged with
## "character_animator_generated". Regeneration only ever replaces generated
## content; anything a user added by hand is left alone.

const GENERATED_META := "character_animator_generated"
const SCHEMA_META := "character_animator_schema_version"
const SCHEMA_VERSION := 1


## Builds the graph under `target`. Returns a dictionary with:
##   animation_player, animation_tree, created_animations, warnings
static func build(target: Node, profile: CharacterAnimationProfile) -> Dictionary:
	var result := {
		"animation_player": null,
		"animation_tree": null,
		"created_animations": [],
		"warnings": [],
	}
	if target == null or profile == null:
		return result

	var animator := _resolve_animator(target, profile)

	var player := _get_or_create_animation_player(target)
	_clear_animations(player)
	var library := _get_or_create_library(player)

	for clip_name in profile.animation_names():
		if clip_name == &"":
			continue
		var animation := _build_animation(animator, clip_name, player)
		if animation == null:
			animation = _empty_animation()
			result["warnings"].append(
				"No source found for clip '%s'; created a placeholder animation." % clip_name)
		library.add_animation(String(clip_name), animation)
		result["created_animations"].append(clip_name)

	var tree := _get_or_create_tree(target)
	tree.anim_player = target.get_path_to(player)
	tree.tree_root = _build_state_machine(profile, library)
	tree.root_node = NodePath("parameters/playback")
	tree.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_PHYSICS
	tree.active = true

	result["animation_player"] = player
	result["animation_tree"] = tree
	return result


## Removes nodes previously created by this builder and stops playback.
static func clear_generated(target: Node) -> void:
	if target == null:
		return
	var player := target.get_node_or_null("AnimationPlayer")
	if player != null and bool(player.get_meta(GENERATED_META, false)):
		target.remove_child(player)
		player.queue_free()
	var tree := target.get_node_or_null("AnimationTree")
	if tree != null and bool(tree.get_meta(GENERATED_META, false)):
		tree.active = false
		target.remove_child(tree)
		tree.queue_free()


static func _resolve_animator(target: Node, profile: CharacterAnimationProfile) -> Sprite2D:
	if profile.animator_path != NodePath():
		var node := target.get_node_or_null(profile.animator_path)
		if node is Sprite2D:
			return node
	for child in target.get_children():
		if child is CharacterAnimator:
			return child
	return null


static func _get_or_create_animation_player(target: Node) -> AnimationPlayer:
	var player := target.get_node_or_null("AnimationPlayer") as AnimationPlayer
	if player == null:
		player = AnimationPlayer.new()
		player.name = "AnimationPlayer"
		target.add_child(player)
		_mark_generated(player)
	return player


static func _clear_animations(player: AnimationPlayer) -> void:
	for lib_name in player.get_animation_library_list():
		player.remove_animation_library(lib_name)


static func _get_or_create_library(player: AnimationPlayer) -> AnimationLibrary:
	for lib_name in player.get_animation_library_list():
		var library := player.get_animation_library(lib_name)
		if library != null:
			return library
	var library := AnimationLibrary.new()
	player.add_animation_library("", library)
	return library


static func _get_or_create_tree(target: Node) -> AnimationTree:
	var tree := target.get_node_or_null("AnimationTree") as AnimationTree
	if tree == null:
		tree = AnimationTree.new()
		tree.name = "AnimationTree"
		target.add_child(tree)
		_mark_generated(tree)
	return tree


static func _build_animation(animator: Sprite2D, clip_name: StringName, player: AnimationPlayer) -> Animation:
	var clip := _find_clip(animator, clip_name)
	if clip == null or clip.frames.is_empty():
		return null
	var animation := Animation.new()
	animation.loop_mode = Animation.LOOP_LINEAR if clip.loop else Animation.LOOP_NONE
	animation.length = clip.duration()
	var track := animation.add_track(Animation.TYPE_VALUE)
	animation.track_set_path(track, _track_path(animator, player))
	animation.track_set_interpolation_type(track, Animation.INTERPOLATION_NEAREST)
	var t := 0.0
	var step := 1.0 / maxf(clip.fps, 0.001)
	for region in clip.frames:
		animation.track_insert_key(track, t, region)
		t += step
	return animation


static func _track_path(animator: Sprite2D, player: AnimationPlayer) -> NodePath:
	var root: Node = player
	if player.root_node != NodePath():
		root = player.get_node_or_null(player.root_node)
	if root == null:
		root = player.get_parent()
	if root == null:
		root = player
	var rel := String(root.get_path_to(animator))
	return NodePath(rel + ":region_rect")


static func _find_clip(animator: Sprite2D, clip_name: StringName) -> AnimationClip:
	if animator == null or not animator.has_method("get_clip"):
		return null
	return animator.get_clip(clip_name) as AnimationClip


static func _empty_animation() -> Animation:
	var animation := Animation.new()
	animation.length = 0.01
	return animation


static func _build_state_machine(profile: CharacterAnimationProfile, library: AnimationLibrary) -> AnimationNodeStateMachine:
	var sm := AnimationNodeStateMachine.new()

	var locomotion := AnimationNodeBlendSpace1D.new()
	var has_idle := library.has_animation(String(profile.idle))
	var has_walk := library.has_animation(String(profile.walk))
	var has_run := library.has_animation(String(profile.run))
	if has_idle:
		locomotion.add_blend_point(_leaf(profile.idle), 0.0)
	if has_walk and profile.walk_point > 0.0:
		locomotion.add_blend_point(_leaf(profile.walk), profile.walk_point)
	if has_run and profile.run_point > profile.walk_point:
		locomotion.add_blend_point(_leaf(profile.run), profile.run_point)
	sm.add_node("Locomotion", locomotion, Vector2(0, 0))

	sm.add_node("Jump", _leaf(profile.jump), Vector2(0, 160))
	sm.add_node("Fall", _leaf(profile.fall), Vector2(170, 160))
	if profile.land != &"" and library.has_animation(String(profile.land)):
		sm.add_node("Land", _leaf(profile.land), Vector2(340, 160))

	var has_crouch := (
		(profile.crouch_idle != &"" and library.has_animation(String(profile.crouch_idle)))
		or (profile.crouch_move != &"" and library.has_animation(String(profile.crouch_move)))
	)
	if has_crouch:
		sm.add_node("CrouchIdle", _leaf(profile.crouch_idle), Vector2(-180, 160))
		if profile.crouch_move != &"" and library.has_animation(String(profile.crouch_move)):
			sm.add_node("CrouchMove", _leaf(profile.crouch_move), Vector2(-180, 320))

	_add_condition_transition(sm, "Locomotion", "Jump", "rising", profile)
	_add_condition_transition(sm, "Jump", "Fall", "falling", profile)
	if sm.has_node("Land"):
		_add_condition_transition(sm, "Fall", "Land", "grounded", profile)
		sm.add_transition("Land", "Locomotion", _auto_transition(profile))
	else:
		_add_condition_transition(sm, "Fall", "Locomotion", "grounded", profile)
	if has_crouch:
		_add_condition_transition(sm, "Locomotion", "CrouchIdle", "crouching", profile)
		if sm.has_node("CrouchMove"):
			_add_condition_transition(sm, "CrouchIdle", "CrouchMove", "moving", profile)
			_add_condition_transition(sm, "CrouchMove", "CrouchIdle", "stopped", profile)
		_add_condition_transition(sm, "CrouchIdle", "Locomotion", "standing", profile)
		if sm.has_node("CrouchMove"):
			_add_condition_transition(sm, "CrouchMove", "Locomotion", "standing", profile)
	return sm


static func _leaf(animation: StringName) -> AnimationNodeAnimation:
	var node := AnimationNodeAnimation.new()
	node.animation = animation
	return node


static func _add_condition_transition(
	sm: AnimationNodeStateMachine,
	from_state: StringName,
	to_state: StringName,
	condition: StringName,
	profile: CharacterAnimationProfile,
) -> void:
	var transition := AnimationNodeStateMachineTransition.new()
	transition.switch_mode = AnimationNodeStateMachineTransition.SWITCH_MODE_IMMEDIATE
	transition.xfade_time = profile.transition_blend_time
	transition.advance_mode = AnimationNodeStateMachineTransition.ADVANCE_MODE_AUTO
	_set_condition(transition, condition)
	sm.add_transition(from_state, to_state, transition)


static func _auto_transition(profile: CharacterAnimationProfile) -> AnimationNodeStateMachineTransition:
	var transition := AnimationNodeStateMachineTransition.new()
	transition.switch_mode = AnimationNodeStateMachineTransition.SWITCH_MODE_AT_END
	transition.xfade_time = profile.transition_blend_time
	transition.advance_mode = AnimationNodeStateMachineTransition.ADVANCE_MODE_AUTO
	return transition


static func _set_condition(transition: AnimationNodeStateMachineTransition, condition: StringName) -> void:
	if transition.has_method("add_transition_condition"):
		transition.add_transition_condition(condition)
	else:
		transition.advance_condition = condition


static func _mark_generated(node: Node) -> void:
	node.set_meta(GENERATED_META, true)
	node.set_meta(SCHEMA_META, SCHEMA_VERSION)
