class_name AnimationController
extends Node

signal animation_finished(animation_id: String)

var _sprite: AnimatedSprite2D
var _manifest_index: Dictionary = {}
var _sprite_importer := SpriteImporter.new()


func inject_sprite(sprite: AnimatedSprite2D) -> void:
	_sprite = sprite


func load_manifest(manifest_index: Dictionary) -> void:
	_manifest_index = manifest_index


func play(animation_id: String, duration_override: float = -1.0) -> void:
	if not _manifest_index.has(animation_id):
		push_error("AnimationController: unknown animation id '%s'" % animation_id)
		return

	var clip: Dictionary = _manifest_index[animation_id]

	if _sprite != null:
		_sprite.sprite_frames = _sprite_importer.load_sprite_frames(clip)
		_sprite.play(animation_id)

	var loop: bool = clip.get("loop", false)
	var wait_duration := -1.0
	if duration_override >= 0.0:
		wait_duration = duration_override
	elif not loop:
		wait_duration = float(clip.frame_count) / float(clip.fps)

	if wait_duration >= 0.0:
		await get_tree().create_timer(wait_duration).timeout
		animation_finished.emit(animation_id)
