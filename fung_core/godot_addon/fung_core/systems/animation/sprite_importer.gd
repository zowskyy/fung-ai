class_name SpriteImporter
extends RefCounted


func load_sprite_frames(clip: Dictionary) -> SpriteFrames:
	var frames := SpriteFrames.new()
	if frames.has_animation("default"):
		frames.remove_animation("default")
	frames.add_animation(clip.id)
	frames.set_animation_speed(clip.id, clip.fps)
	frames.set_animation_loop(clip.id, clip.get("loop", false))

	if not ResourceLoader.exists(clip.sprite_sheet):
		push_warning("SpriteImporter: sprite sheet not found for clip '%s': %s" % [clip.id, clip.sprite_sheet])
		return frames

	var texture := load(clip.sprite_sheet) as Texture2D
	if texture == null:
		push_warning("SpriteImporter: could not load '%s' as a Texture2D for clip '%s'" % [clip.sprite_sheet, clip.id])
		return frames

	frames.add_frame(clip.id, texture)
	return frames
