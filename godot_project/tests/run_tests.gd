extends SceneTree
## Headless test runner for the 2D Character Animator plugin.
##
## Run from the godot_project directory:
##   godot --headless --path . --script res://tests/run_tests.gd
##
## Exits 0 when everything passes, 1 otherwise.

const AnimationClip := preload("res://addons/character_animator/runtime/animation_clip.gd")
const CharacterAnimator := preload("res://addons/character_animator/runtime/character_animator.gd")
const CharacterAnimationProfile := preload("res://addons/character_animator/runtime/character_animation_profile.gd")
const CharacterAnimationDriver := preload("res://addons/character_animator/runtime/character_animation_driver.gd")
const AnimationEventReceiver := preload("res://addons/character_animator/runtime/animation_event_receiver.gd")
const CharacterSkeleton := preload("res://addons/character_animator/runtime/character_skeleton.gd")
const CharacterRig := preload("res://addons/character_animator/runtime/character_rig.gd")
const BoneDef := preload("res://addons/character_animator/runtime/bone_def.gd")
const BoneClip := preload("res://addons/character_animator/runtime/bone_clip.gd")
const BoneTrack := preload("res://addons/character_animator/runtime/bone_track.gd")
const BoneKey := preload("res://addons/character_animator/runtime/bone_key.gd")
const SkeletonAnimator := preload("res://addons/character_animator/runtime/skeleton_animator.gd")
const SpriteSheetFactory := preload("res://addons/character_animator/runtime/sprite_sheet_factory.gd")
const AnimationGraphBuilder := preload("res://addons/character_animator/editor/animation_graph_builder.gd")
const AnimationValidator := preload("res://addons/character_animator/editor/animation_validator.gd")
const ValidationIssue := preload("res://addons/character_animator/editor/validation_issue.gd")
const CharacterSceneScanner := preload("res://addons/character_animator/editor/character_scene_scanner.gd")

var _passes := 0
var _failures := 0


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	print("=== Character Animator plugin tests ===")
	await _test_animation_clip()
	await _test_character_animator()
	await _test_profile()
	await _test_builder_and_state_machine()
	await _test_skeleton_animator()
	await _test_validator()
	await _test_event_receiver()
	await _test_scanner()
	print("")
	print("RESULTS: %d passed, %d failed" % [_passes, _failures])
	if _failures > 0:
		print("FAILED")
		quit(1)
	else:
		print("ALL TESTS PASSED")
		quit(0)


func check(condition: bool, label: String) -> void:
	if condition:
		_passes += 1
	else:
		_failures += 1
		print("FAIL: %s" % label)


func _wait_frames(count: int) -> void:
	for i in count:
		await physics_frame


# ---------------------------------------------------------------- tests

func _test_animation_clip() -> void:
	var clip: AnimationClip = AnimationClip.new()
	clip.name = &"test"
	clip.add_frame(Rect2(0, 0, 10, 10))
	clip.add_frame(Rect2(10, 0, 10, 10))
	clip.add_frame(Rect2(20, 0, 10, 10))
	clip.fps = 10.0
	check(clip.frame_count() == 3, "AnimationClip.frame_count")
	check(is_equal_approx(clip.duration(), 0.3), "AnimationClip.duration = frames / fps")
	clip.move_frame(0, 2)
	check(clip.frame_rect(2) == Rect2(0, 0, 10, 10), "AnimationClip.move_frame reorders")
	clip.insert_frame(1, Rect2(30, 0, 10, 10))
	check(clip.frame_count() == 4, "AnimationClip.insert_frame")
	clip.remove_frame(3)
	check(clip.frame_count() == 3, "AnimationClip.remove_frame")
	check(clip.frame_rect(99) == clip.frames[2], "AnimationClip.frame_rect clamps")


func _test_character_animator() -> void:
	var animator: CharacterAnimator = CharacterAnimator.new()
	animator.texture = SpriteSheetFactory.generate_character_sheet()
	animator.auto_play = false
	root.add_child(animator)

	var clip: AnimationClip = AnimationClip.new()
	clip.name = &"idle"
	clip.frames = [Rect2(0, 0, 48, 48), Rect2(48, 0, 48, 48), Rect2(96, 0, 48, 48)]
	clip.fps = 20.0
	clip.loop = true
	animator.clips[&"idle"] = clip
	animator.play(&"idle")
	check(animator.is_playing, "animator is playing")
	check(animator.frame_index == 0, "animator starts at frame 0")
	check(animator.region_enabled, "animator enabled region rendering")
	animator.advance(0.06)
	check(animator.frame_index > 0, "animator advanced frames (now %d)" % animator.frame_index)
	check(animator.is_playing, "looping clip keeps playing")

	var one_shot: AnimationClip = AnimationClip.new()
	one_shot.name = &"one"
	one_shot.frames = [Rect2(0, 0, 48, 48)]
	one_shot.fps = 20.0
	one_shot.loop = false
	animator.clips[&"one"] = one_shot
	var finished := [false]
	animator.animation_finished.connect(func(_name: StringName): finished[0] = true)
	animator.play(&"one")
	animator.advance(0.1)
	check(not animator.is_playing, "non-loop clip stops")
	check(finished[0], "non-loop clip emits animation_finished")
	check(animator.region_rect == Rect2(0, 0, 48, 48), "animator applied the last frame region")
	animator.queue_free()


func _test_profile() -> void:
	var profile: CharacterAnimationProfile = CharacterAnimationProfile.new()
	profile.idle = &"idle"
	profile.run = &"run"
	check(profile.animation_names().size() == 10, "profile exposes all semantic roles")
	check(profile.required_animation_names() == PackedStringArray([&"idle", &"run", &"jump", &"fall"]),
		"profile required roles")
	check(profile.has_clip_role(&"crouch_walk"), "profile recognizes stance roles")


func _test_builder_and_state_machine() -> void:
	var target := Node2D.new()
	target.name = "TreeCharacter"
	root.add_child(target)

	var animator: CharacterAnimator = CharacterAnimator.new()
	animator.name = "CharacterAnimator"
	animator.auto_play = false
	animator.texture = SpriteSheetFactory.generate_character_sheet()
	target.add_child(animator)
	_build_demo_clips(animator)

	var profile: CharacterAnimationProfile = CharacterAnimationProfile.new()
	profile.animator_path = target.get_path_to(animator)
	profile.idle = &"idle"
	profile.walk = &"walk"
	profile.run = &"run"
	profile.jump = &"jump"
	profile.fall = &"fall"
	profile.land = &"land"
	profile.crouch_idle = &"crouch_idle"
	profile.crouch_move = &"crouch_walk"

	var result := AnimationGraphBuilder.build(target, profile)
	var tree := result["animation_tree"] as AnimationTree
	var player := result["animation_player"] as AnimationPlayer
	check(tree != null, "builder created an AnimationTree")
	check(player != null, "builder created an AnimationPlayer")
	check(player != null and player.has_animation("idle"), "player library has idle")
	check(player != null and player.has_animation("crouch_walk"), "player library has crouch_walk")
	check(tree != null and tree.tree_root != null, "tree has a root state machine")
	check(tree != null and tree.root_node == NodePath("parameters/playback"), "tree root_node is the playback parameter")

	var driver: CharacterAnimationDriver = CharacterAnimationDriver.new()
	driver.name = "CharacterAnimationDriver"
	driver.animation_tree = tree
	driver.profile = profile
	driver.visuals = animator
	target.add_child(driver)

	driver.update_locomotion(Vector2(0, 0), true, false, true)
	await _wait_frames(6)
	var state := driver.current_state_name()
	check(state == "Locomotion", "grounded idle is in Locomotion (state=%s)" % state)

	driver.update_locomotion(Vector2(50, -200), false, false, true)
	await _wait_frames(10)
	state = driver.current_state_name()
	check(state == "Jump", "rising condition moves to Jump (state=%s)" % state)

	driver.update_locomotion(Vector2(50, 150), false, false, true)
	await _wait_frames(10)
	state = driver.current_state_name()
	check(state == "Fall", "falling condition moves to Fall (state=%s)" % state)

	driver.update_locomotion(Vector2(50, 0), true, false, true)
	await _wait_frames(12)
	state = driver.current_state_name()
	check(state == "Land" or state == "Locomotion",
		"landing edge travels through Land back to Locomotion (state=%s)" % state)

	driver.update_locomotion(Vector2(30, 0), true, true, true)
	await _wait_frames(10)
	state = driver.current_state_name()
	check(state == "CrouchIdle" or state == "CrouchMove",
		"crouching condition enters a crouch state (state=%s)" % state)

	driver.update_locomotion(Vector2(30, 0), true, false, true)
	await _wait_frames(10)
	state = driver.current_state_name()
	check(state == "Locomotion", "standing condition returns to Locomotion (state=%s)" % state)

	driver.request_state(&"Jump")
	await _wait_frames(4)
	state = driver.current_state_name()
	check(state == "Jump", "request_state travels to a named state (state=%s)" % state)

	driver.queue_free()
	target.queue_free()


func _build_demo_clips(animator: CharacterAnimator) -> void:
	var spec := {
		&"idle": [Vector2i(0, 0), Vector2i(1, 0), Vector2i(2, 0), Vector2i(3, 0)],
		&"walk": [Vector2i(0, 1), Vector2i(1, 1), Vector2i(2, 1), Vector2i(3, 1), Vector2i(4, 1), Vector2i(5, 1), Vector2i(6, 1), Vector2i(7, 1)],
		&"run": [Vector2i(0, 1), Vector2i(1, 1), Vector2i(2, 1), Vector2i(3, 1), Vector2i(4, 1), Vector2i(5, 1), Vector2i(6, 1), Vector2i(7, 1)],
		&"jump": [Vector2i(0, 2), Vector2i(1, 2)],
		&"fall": [Vector2i(2, 2), Vector2i(3, 2)],
		&"land": [Vector2i(4, 2), Vector2i(5, 2)],
		&"crouch_idle": [Vector2i(0, 3), Vector2i(1, 3)],
		&"crouch_walk": [Vector2i(2, 3), Vector2i(3, 3), Vector2i(4, 3), Vector2i(5, 3)],
	}
	for clip_name in spec:
		var clip: AnimationClip = AnimationClip.new()
		clip.name = clip_name
		for cell in spec[clip_name]:
			clip.add_frame(Rect2(48.0 * float(cell.x), 48.0 * float(cell.y), 48.0, 48.0))
		clip.fps = 10.0
		clip.loop = clip_name in [&"idle", &"walk", &"run", &"crouch_idle", &"crouch_walk"]
		animator.clips[clip_name] = clip


func _test_skeleton_animator() -> void:
	var target := Node2D.new()
	target.name = "SkeletonCharacter"
	root.add_child(target)

	var skeleton: CharacterSkeleton = CharacterSkeleton.new()
	skeleton.name = "CharacterSkeleton"
	target.add_child(skeleton)

	var rig: CharacterRig = CharacterRig.new()
	var hip: BoneDef = BoneDef.new()
	hip.bone_name = &"hip"
	rig.add_bone(hip)
	var arm: BoneDef = BoneDef.new()
	arm.bone_name = &"arm"
	arm.parent_bone = &"hip"
	arm.rest_position = Vector2(0, -20)
	rig.add_bone(arm)
	var hand: BoneDef = BoneDef.new()
	hand.bone_name = &"hand"
	hand.parent_bone = &"arm"
	hand.rest_position = Vector2(0, -20)
	rig.add_bone(hand)
	skeleton.rig = rig
	skeleton.build_from_rig(rig)

	check(rig.validate(), "rig.validate accepts a valid hierarchy")
	check(skeleton.has_bone(&"hip") and skeleton.has_bone(&"arm") and skeleton.has_bone(&"hand"),
		"skeleton built all bones")
	check(skeleton.get_bone_node(&"arm") is Bone2D, "bone nodes are Bone2D")
	check(skeleton.get_bone_node(&"hand").get_parent() == skeleton.get_bone_node(&"arm"),
		"bone hierarchy parented correctly")

	var animator: SkeletonAnimator = SkeletonAnimator.new()
	animator.name = "SkeletonAnimator"
	skeleton.add_child(animator)

	var clip: BoneClip = BoneClip.new()
	clip.name = &"wave"
	clip.loop = true
	var track: BoneTrack = BoneTrack.new()
	track.bone_name = &"arm"
	var k0: BoneKey = BoneKey.new()
	k0.time = 0.0
	k0.rotation = 0.0
	var k1: BoneKey = BoneKey.new()
	k1.time = 0.5
	k1.rotation = 1.5
	var k2: BoneKey = BoneKey.new()
	k2.time = 1.0
	k2.rotation = 0.0
	track.add_key(k0)
	track.add_key(k1)
	track.add_key(k2)
	clip.add_track(track)
	check(clip.duration() >= 1.0, "bone clip duration covers its keys")
	animator.clips[&"wave"] = clip
	animator.play(&"wave")
	animator.advance(0.3)
	var bone := skeleton.get_bone_node(&"arm")
	check(absf(bone.rotation) > 0.01, "bone rotation animated by SkeletonAnimator (%.2f)" % bone.rotation)
	check(animator.current_clip == &"wave", "skeleton animator tracks its current clip")

	animator.queue_free()
	target.queue_free()


func _test_validator() -> void:
	var target := Node2D.new()
	target.name = "ValidatedCharacter"
	root.add_child(target)
	var profile: CharacterAnimationProfile = CharacterAnimationProfile.new()
	profile.idle = &"idle"
	profile.run = &"run"
	profile.jump = &"jump"
	profile.fall = &"fall"
	profile.visuals_path = NodePath("Missing/Visuals")
	var issues := AnimationValidator.validate(target, profile)
	var flagged_missing := false
	var flagged_visuals := false
	for issue in issues:
		if issue.severity == ValidationIssue.Severity.ERROR and "Required clip" in issue.message:
			flagged_missing = true
		if issue.severity == ValidationIssue.Severity.WARNING and "Visuals" in issue.message:
			flagged_visuals = true
	check(flagged_missing, "validator flags missing required clips")
	check(flagged_visuals, "validator flags unresolvable visuals path")
	check(not issues.is_empty(), "validator returns structured issues")
	target.queue_free()


func _test_event_receiver() -> void:
	var receiver: AnimationEventReceiver = AnimationEventReceiver.new()
	root.add_child(receiver)
	var received: Array = []
	receiver.animation_event.connect(
		func(event_name: StringName, payload: Variant): received.append([event_name, payload]))
	receiver.emit_event(&"footstep", "left")
	check(received.size() == 1 and received[0][0] == &"footstep" and received[0][1] == "left",
		"event receiver forwards events with payload")
	check(receiver.has_event(&"hitbox_open") and receiver.has_event(&"land"),
		"event receiver exposes the controlled vocabulary")
	receiver.queue_free()


func _test_scanner() -> void:
	var target := Node2D.new()
	target.name = "ScannedCharacter"
	root.add_child(target)
	var body := CharacterBody2D.new()
	body.name = "Body"
	target.add_child(body)
	var found := CharacterSceneScanner.scan(target)
	check(not found["bodies"].is_empty(), "scanner finds CharacterBody2D nodes")
	check("Bodies: 1" in CharacterSceneScanner.describe(found), "scanner describe output")
	target.queue_free()
