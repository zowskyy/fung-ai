class_name AnimationManifestLoader
extends RefCounted


func load_from_dict(data: Dictionary) -> Dictionary:
	if not data.has("id") or not data.has("clips"):
		push_error("AnimationManifestLoader: manifest missing required keys 'id' and/or 'clips'")
		return {}

	var clips = data.clips
	if typeof(clips) != TYPE_ARRAY:
		push_error("AnimationManifestLoader: 'clips' must be an array")
		return {}

	var index := {}
	for clip in clips:
		if typeof(clip) != TYPE_DICTIONARY:
			push_error("AnimationManifestLoader: clip entry must be an object")
			return {}
		for key in ["id", "sprite_sheet", "frame_count", "fps"]:
			if not clip.has(key):
				push_error("AnimationManifestLoader: clip missing required key '%s'" % key)
				return {}
		index[clip.id] = clip

	return index
