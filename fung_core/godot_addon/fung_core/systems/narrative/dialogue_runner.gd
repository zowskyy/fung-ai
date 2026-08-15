class_name DialogueRunner
extends RefCounted


func run(beat: Dictionary, tree: SceneTree) -> void:
	await tree.create_timer(beat.get("duration", 1.0)).timeout
