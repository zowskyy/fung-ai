extends Node2D

# Default paths, overridable via command line user args (after "--"):
#   godot --path <project> -- <scene_json_path> <screenshot_output_prefix>
var scene_json_path := "C:/Users/thewi/OneDrive/Desktop/fung.us/godot_project/example_scene.json"
var screenshot_prefix := "C:/Users/thewi/OneDrive/Desktop/fung.us/godot_project/anim_screenshot"

var scene_data: Dictionary = {}
var camera_keyframes: Array = []
var camera_loop := false
var duration_s := 8.0
var elapsed_s := 0.0

var sway_layers: Array = []  # [{node: ParallaxLayer, amplitude_rad: float, speed: float}]
var animated_sprites: Array = []  # [AnimatedSprite2D] built by build_animated_layer(), for external inspection

@onready var parallax: ParallaxBackground = $ParallaxBackground
@onready var camera: Camera2D = $Camera2D


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() >= 1:
		scene_json_path = args[0]
	if args.size() >= 2:
		screenshot_prefix = args[1]

	print("Loading scene JSON from: ", scene_json_path)

	var loaded = load_scene_data(scene_json_path)
	if loaded == null:
		push_error("Failed to load/parse scene JSON at %s" % scene_json_path)
		get_tree().quit(1)
		return

	scene_data = loaded
	build_scene(scene_data)

	# A couple of frames so the first layout/draw settles before we start capturing.
	await get_tree().process_frame
	await get_tree().process_frame

	await capture("%s_t0.png" % screenshot_prefix)
	await get_tree().create_timer(2.0).timeout
	await capture("%s_t2.png" % screenshot_prefix)
	await get_tree().create_timer(4.0).timeout
	await capture("%s_t4.png" % screenshot_prefix)

	get_tree().quit()


func load_scene_data(path: String):
	if not FileAccess.file_exists(path):
		push_error("File does not exist: " + path)
		return null
	var f := FileAccess.open(path, FileAccess.READ)
	var text := f.get_as_text()
	f.close()
	var parsed = JSON.parse_string(text)
	if parsed == null:
		push_error("JSON parse failed for " + path)
		return null
	return parsed


func build_scene(data: Dictionary) -> void:
	duration_s = float(data.get("duration_s", 8.0))

	var base_dir := scene_json_path.get_base_dir()

	var layers: Array = data.get("layers", [])
	for layer in layers:
		# Additive dispatch: a layer with "cels"/"tags" (a real Aseprite/
		# LibreSprite CLI export, converted by tools/aseprite_import.py) gets
		# the AnimatedSprite2D path. Everything else keeps the original
		# static image + sway path exactly as before -- this is a superset,
		# not a replacement, so old scene JSON (example_scene.json) is
		# unaffected.
		if layer.has("cels") and layer.has("tags"):
			build_animated_layer(layer, base_dir)
		else:
			build_static_layer(layer, base_dir)

	var cam: Dictionary = data.get("camera", {})
	camera_keyframes = cam.get("keyframes", [])
	camera_loop = bool(cam.get("loop", false))


func build_static_layer(layer: Dictionary, base_dir: String) -> void:
	var image_rel := String(layer["image"])
	var image_path := image_rel
	if not image_path.is_absolute_path():
		image_path = base_dir.path_join(image_rel)

	var img := Image.new()
	var err := img.load(image_path)
	if err != OK:
		push_error("Failed to load layer image: " + image_path)
		return
	var tex := ImageTexture.create_from_image(img)

	var player := ParallaxLayer.new()
	player.name = String(layer.get("name", "layer"))
	var depth := float(layer.get("depth", 1.0))
	player.motion_scale = Vector2(depth, depth)

	var sprite := Sprite2D.new()
	sprite.texture = tex
	sprite.centered = false
	apply_blend_mode(sprite, layer)
	add_to_parent_with_group(player, sprite, layer)
	parallax.add_child(player)

	var sway: Dictionary = layer.get("sway", {})
	var amp_deg := float(sway.get("amplitude_deg", 0.0))
	var speed := float(sway.get("speed", 0.0))
	if amp_deg != 0.0 and speed != 0.0:
		sway_layers.append({
			"node": player,
			"amplitude_rad": deg_to_rad(amp_deg),
			"speed": speed,
		})


# ---------------------------------------------------------------------------
# Animated (cel/tag) layers -- Phase 1 Direction B + Phase 2 fidelity.
#
# Ping-pong playback choice: Godot's SpriteFrames/AnimatedSprite2D has no
# native ping-pong loop mode (only forward loop or no loop). We build the
# ping-pong frame *sequence* explicitly -- concatenating forward+reverse
# frames into one SpriteFrames animation (e.g. frames 0,1,2,3,2,1 for a
# 4-frame ping_pong tag) and let AnimatedSprite2D loop that sequence
# natively -- rather than driving playback direction manually from
# _process(). This was simpler and just as correct: it reuses Godot's own
# timing/looping instead of reimplementing it, and every AniDir mode reduces
# to "the ordered list of frame indices to play once through, then loop".
# ---------------------------------------------------------------------------

const BLEND_MODE_MAP := {
	"normal": CanvasItemMaterial.BLEND_MODE_MIX,
	"multiply": CanvasItemMaterial.BLEND_MODE_MUL,
	"lighten": CanvasItemMaterial.BLEND_MODE_ADD,
	"color_dodge": CanvasItemMaterial.BLEND_MODE_ADD,
	"difference": CanvasItemMaterial.BLEND_MODE_SUB,
	"exclusion": CanvasItemMaterial.BLEND_MODE_SUB,
	# Aseprite blend modes with no direct Godot CanvasItemMaterial equivalent
	# (screen, overlay, darken, color_burn, hard_light, soft_light, the HSL_*
	# modes) fall back to normal/MIX -- a documented gap, not a silent bug.
}


func apply_blend_mode(node: CanvasItem, layer: Dictionary) -> void:
	var blend_str := String(layer.get("blend_mode", "normal"))
	if blend_str == "" or blend_str == "normal":
		return
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = BLEND_MODE_MAP.get(blend_str, CanvasItemMaterial.BLEND_MODE_MIX)
	node.material = mat


func add_to_parent_with_group(parent: Node, child: Node2D, layer: Dictionary) -> void:
	# Phase 2: preserve meta.layers[].group as nested Node2D structure
	# instead of flattening every layer directly under its ParallaxLayer.
	# group is a "/"-separated path, e.g. "environment/torches".
	var group_path := String(layer.get("group", ""))
	if group_path == "":
		parent.add_child(child)
		return

	var current: Node = parent
	for part in group_path.split("/"):
		if part == "":
			continue
		var existing := current.get_node_or_null(part)
		if existing == null:
			existing = Node2D.new()
			existing.name = part
			current.add_child(existing)
		current = existing
	current.add_child(child)


func build_animated_layer(layer: Dictionary, base_dir: String) -> void:
	var sheet_rel := String(layer.get("spritesheet", ""))
	var sheet_path := sheet_rel
	if not sheet_path.is_absolute_path():
		sheet_path = base_dir.path_join(sheet_rel)

	var img := Image.new()
	var err := img.load(sheet_path)
	if err != OK:
		push_error("Failed to load layer spritesheet: " + sheet_path)
		return
	var sheet_tex := ImageTexture.create_from_image(img)

	var cels: Array = layer.get("cels", [])
	var tags: Array = layer.get("tags", [])

	var frames := SpriteFrames.new()
	frames.remove_animation("default")  # SpriteFrames always starts with one

	for tag in tags:
		build_tag_animation(frames, sheet_tex, cels, tag)

	var player := ParallaxLayer.new()
	player.name = String(layer.get("name", "animated_layer"))
	var depth := float(layer.get("depth", 1.0))
	player.motion_scale = Vector2(depth, depth)

	var anim_sprite := AnimatedSprite2D.new()
	anim_sprite.sprite_frames = frames
	anim_sprite.centered = false
	apply_blend_mode(anim_sprite, layer)

	add_to_parent_with_group(player, anim_sprite, layer)
	parallax.add_child(player)
	animated_sprites.append(anim_sprite)

	# play() must happen after the node is inside the scene tree -- an
	# AnimatedSprite2D started before entering the tree never advances its
	# frame timer.
	#
	# IMPORTANT: do NOT pre-set `anim_sprite.animation` before calling
	# play(name) here. AnimatedSprite2D.play() only recalculates its internal
	# per-frame speed scale (which is derived from each frame's `duration`)
	# when it detects the animation name is *changing* (`name != animation`).
	# Pre-assigning `.animation` to the same name we're about to play() (or
	# relying on it defaulting to "default", which collides with our
	# synthesized untagged-sprite tag also named "default") makes that check
	# see no change, so the speed scale is silently left at its 1.0 default --
	# every frame then plays at ~1s regardless of its real `duration_ms`.
	# Confirmed by reading AnimatedSprite2D::play()/set_frame_and_progress()
	# in Godot's own source and reproducing the exact 1.0-vs-1/duration
	# discrepancy empirically. The fix is to force a recalculation explicitly
	# via set_frame_and_progress(0, 0.0) right after play().
	if tags.size() > 0:
		var first_tag_name := String(tags[0].get("name", "default"))
		anim_sprite.play(first_tag_name)
		anim_sprite.set_frame_and_progress(0, 0.0)
		var repeat := int(tags[0].get("repeat", 0))
		if repeat > 0:
			bind_finite_repeat(anim_sprite, first_tag_name, repeat)


func build_tag_animation(frames: SpriteFrames, sheet_tex: Texture2D, cels: Array, tag: Dictionary) -> void:
	var tag_name := String(tag.get("name", "default"))
	var from_idx := int(tag.get("from", 0))
	var to_idx := int(tag.get("to", max(0, cels.size() - 1)))
	var direction := String(tag.get("direction", "forward"))

	var frame_order := build_frame_order(from_idx, to_idx, direction)

	frames.add_animation(tag_name)
	frames.set_animation_speed(tag_name, 1.0)  # 1.0 fps baseline; per-frame duration below is in seconds
	frames.set_animation_loop(tag_name, true)

	for idx in frame_order:
		if idx < 0 or idx >= cels.size():
			continue
		var cel: Dictionary = cels[idx]
		var region := Rect2(float(cel.get("x", 0)), float(cel.get("y", 0)), float(cel.get("w", 1)), float(cel.get("h", 1)))
		var atlas := AtlasTexture.new()
		atlas.atlas = sheet_tex
		atlas.region = region
		var duration_ms := float(cel.get("duration_ms", 100))
		frames.add_frame(tag_name, atlas, duration_ms / 1000.0)


func build_frame_order(from_idx: int, to_idx: int, direction: String) -> Array:
	var forward_seq: Array = []
	for i in range(from_idx, to_idx + 1):
		forward_seq.append(i)

	match direction:
		"reverse":
			var rev: Array = forward_seq.duplicate()
			rev.reverse()
			return rev
		"ping_pong":
			var seq: Array = forward_seq.duplicate()
			for i in range(forward_seq.size() - 2, 0, -1):
				seq.append(forward_seq[i])
			return seq
		"ping_pong_reverse":
			var rev2: Array = forward_seq.duplicate()
			rev2.reverse()
			var seq2: Array = rev2.duplicate()
			for i in range(rev2.size() - 2, 0, -1):
				seq2.append(rev2[i])
			return seq2
		_:  # "forward" and any unrecognized direction
			return forward_seq


func bind_finite_repeat(anim_sprite: AnimatedSprite2D, anim_name: String, repeat_count: int) -> void:
	# Godot's AnimatedSprite2D loop flag is binary (loop forever / play once).
	# Tags with a nonzero `repeat` need "loop N times then stop" -- there's no
	# native support for that, so we count completed loops via the
	# animation_finished signal (only emitted for non-looping animations) by
	# temporarily re-triggering play() until the count is reached.
	var state := {"plays": 0}
	anim_sprite.sprite_frames.set_animation_loop(anim_name, false)
	anim_sprite.animation_finished.connect(func():
		state["plays"] += 1
		if state["plays"] < repeat_count:
			anim_sprite.play(anim_name)
	)


func _process(delta: float) -> void:
	elapsed_s += delta

	var t := elapsed_s
	if camera_loop and duration_s > 0.0:
		t = fmod(elapsed_s, duration_s)

	for entry in sway_layers:
		var player: ParallaxLayer = entry["node"]
		for child in player.get_children():
			if child is Sprite2D:
				child.rotation = sin(elapsed_s * entry["speed"]) * entry["amplitude_rad"]

	apply_camera(t)


func apply_camera(t: float) -> void:
	if camera_keyframes.is_empty():
		return
	if camera_keyframes.size() == 1:
		var kf0: Dictionary = camera_keyframes[0]
		camera.position = Vector2(float(kf0.get("x", 0.0)), float(kf0.get("y", 0.0)))
		camera.zoom = Vector2.ONE * float(kf0.get("zoom", 1.0))
		return

	var prev: Dictionary = camera_keyframes[0]
	var next: Dictionary = camera_keyframes[camera_keyframes.size() - 1]
	for i in range(camera_keyframes.size() - 1):
		var a: Dictionary = camera_keyframes[i]
		var b: Dictionary = camera_keyframes[i + 1]
		if t >= float(a["t"]) and t <= float(b["t"]):
			prev = a
			next = b
			break

	var span := float(next["t"]) - float(prev["t"])
	var f := 0.0
	if span > 0.0:
		f = clamp((t - float(prev["t"])) / span, 0.0, 1.0)

	var x: float = lerp(float(prev.get("x", 0.0)), float(next.get("x", 0.0)), f)
	var y: float = lerp(float(prev.get("y", 0.0)), float(next.get("y", 0.0)), f)
	var zoom: float = lerp(float(prev.get("zoom", 1.0)), float(next.get("zoom", 1.0)), f)

	camera.position = Vector2(x, y)
	camera.zoom = Vector2.ONE * zoom


func capture(path: String) -> void:
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	var err := img.save_png(path)
	if err == OK:
		print("Screenshot saved to: ", path)
	else:
		push_error("Failed to save screenshot, error code: %s" % err)
