extends Node2D
## Demo scene controller. Builds placeholder art, frame clips, the generated
## AnimationTree + driver for the player, and a skeletal NPC, all at runtime
## so no binary assets are required.

const FRAME := 48.0

@onready var player := $Player
@onready var animator := $Player/Visuals/CharacterAnimator
@onready var visuals := $Player/Visuals
@onready var driver := $Player/CharacterAnimationDriver
@onready var skeleton := $SkeletonNPC
@onready var skeleton_animator := $SkeletonNPC/SkeletonAnimator


func _ready() -> void:
	_setup_inputs()
	_setup_player_animation()
	_setup_skeleton()


func _setup_inputs() -> void:
	_add_key_action("move_left", [KEY_A, KEY_LEFT])
	_add_key_action("move_right", [KEY_D, KEY_RIGHT])
	_add_key_action("jump", [KEY_SPACE, KEY_W, KEY_UP])
	_add_key_action("crouch", [KEY_S, KEY_DOWN])


func _add_key_action(action: String, keys: Array) -> void:
	if not InputMap.has_action(action):
		InputMap.add_action(action)
	for key in keys:
		var event := InputEventKey.new()
		event.keycode = key
		InputMap.action_add_event(action, event)


func _setup_player_animation() -> void:
	var sheet := SpriteSheetFactory.generate_character_sheet()
	animator.texture = sheet
	animator.auto_play = false
	_build_clips()

	var profile := CharacterAnimationProfile.new()
	profile.animator_path = player.get_path_to(animator)
	profile.visuals_path = player.get_path_to(visuals)
	profile.idle = &"idle"
	profile.walk = &"walk"
	profile.run = &"run"
	profile.jump = &"jump"
	profile.fall = &"fall"
	profile.land = &"land"
	profile.crouch_idle = &"crouch_idle"
	profile.crouch_move = &"crouch_walk"

	var result := AnimationGraphBuilder.build(player, profile)
	driver.profile = profile
	driver.animation_tree = result["animation_tree"] as AnimationTree
	driver.visuals = visuals


func _build_clips() -> void:
	_add_clip(&"idle", _row_frames(0, 4), 6.0, true)
	_add_clip(&"walk", _row_frames(1, 8), 12.0, true)
	_add_clip(&"run", _row_frames(1, 8), 16.0, true)
	_add_clip(&"jump", _rects([Vector2i(0, 2), Vector2i(1, 2)]), 8.0, false)
	_add_clip(&"fall", _rects([Vector2i(2, 2), Vector2i(3, 2)]), 8.0, false)
	_add_clip(&"land", _rects([Vector2i(4, 2), Vector2i(5, 2)]), 10.0, false)
	_add_clip(&"crouch_idle", _rects([Vector2i(0, 3), Vector2i(1, 3)]), 5.0, true)
	_add_clip(&"crouch_walk", _rects([Vector2i(2, 3), Vector2i(3, 3), Vector2i(4, 3), Vector2i(5, 3)]), 10.0, true)


func _add_clip(clip_name: StringName, frames: Array, fps: float, loop: bool) -> void:
	var clip := AnimationClip.new()
	clip.name = clip_name
	for rect in frames:
		clip.add_frame(rect)
	clip.fps = fps
	clip.loop = loop
	animator.clips[clip_name] = clip


func _row_frames(row: int, count: int) -> Array:
	var out: Array = []
	for i in count:
		out.append(Rect2(FRAME * float(i), FRAME * float(row), FRAME, FRAME))
	return out


func _rects(cells: Array) -> Array:
	var out: Array = []
	for cell in cells:
		out.append(Rect2(FRAME * float(cell.x), FRAME * float(cell.y), FRAME, FRAME))
	return out


func _setup_skeleton() -> void:
	var rig := CharacterRig.new()
	_bone(rig, &"hip", &"", Vector2.ZERO, Color(0, 0, 0, 0))
	_bone(rig, &"torso", &"hip", Vector2(0, -22), Color(0.22, 0.55, 0.85))
	_bone(rig, &"head", &"torso", Vector2(0, -18), Color(0.93, 0.78, 0.55))
	_bone(rig, &"arm_r", &"torso", Vector2(12, -6), Color(0.30, 0.28, 0.62))
	_bone(rig, &"arm_l", &"torso", Vector2(-12, -6), Color(0.30, 0.28, 0.62))
	_bone(rig, &"leg_l", &"hip", Vector2(-7, 0), Color(0.22, 0.55, 0.85))
	_bone(rig, &"leg_r", &"hip", Vector2(7, 0), Color(0.22, 0.55, 0.85))
	skeleton.rig = rig
	skeleton.build_from_rig(rig)

	var clip := BoneClip.new()
	clip.name = &"wave"
	clip.loop = true
	var track := BoneTrack.new()
	track.bone_name = &"arm_r"
	var k0 := BoneKey.new()
	k0.time = 0.0
	k0.rotation = deg_to_rad(-40.0)
	var k1 := BoneKey.new()
	k1.time = 0.5
	k1.rotation = deg_to_rad(30.0)
	var k2 := BoneKey.new()
	k2.time = 1.0
	k2.rotation = deg_to_rad(-40.0)
	track.add_key(k0)
	track.add_key(k1)
	track.add_key(k2)
	clip.add_track(track)
	skeleton_animator.clips[&"wave"] = clip
	skeleton_animator.initial_clip = &"wave"
	skeleton_animator.auto_play = true


func _bone(rig: CharacterRig, bone_name: StringName, parent_bone: StringName, rest: Vector2, color: Color) -> void:
	var def := BoneDef.new()
	def.bone_name = bone_name
	def.parent_bone = parent_bone
	def.rest_position = rest
	if color.a > 0.0:
		def.sprite_texture = SpriteSheetFactory.solid_texture(Vector2i(20, 22), color)
	rig.add_bone(def)
