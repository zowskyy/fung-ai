@tool
class_name CharacterSceneScanner
extends RefCounted
## Walks a scene tree and reports the animation-relevant nodes found, so the
## setup wizard can offer concrete choices instead of silently guessing.

static func scan(root: Node) -> Dictionary:
	var result := {
		"bodies": [],          # CharacterBody2D
		"animators": [],       # CharacterAnimator (clips-capable Sprite2D)
		"sprites": [],         # plain Sprite2D
		"animated_sprites": [],# AnimatedSprite2D
		"players": [],         # AnimationPlayer
		"trees": [],           # AnimationTree
		"skeletons": [],       # CharacterSkeleton
		"skeleton_animators": [],
	}
	if root == null:
		return result
	_scan_node(root, result)
	return result


static func _scan_node(node: Node, result: Dictionary) -> void:
	if node is CharacterAnimator:
		result["animators"].append(node)
	elif node is AnimatedSprite2D:
		result["animated_sprites"].append(node)
	elif node is Sprite2D:
		result["sprites"].append(node)
	if node is CharacterBody2D:
		result["bodies"].append(node)
	if node is AnimationPlayer:
		result["players"].append(node)
	if node is AnimationTree:
		result["trees"].append(node)
	if node is CharacterSkeleton:
		result["skeletons"].append(node)
	if node is SkeletonAnimator:
		result["skeleton_animators"].append(node)
	for child in node.get_children():
		_scan_node(child, result)


static func describe(scan_result: Dictionary) -> String:
	var lines := PackedStringArray()
	lines.append("Bodies: %d" % scan_result["bodies"].size())
	lines.append("CharacterAnimators: %d" % scan_result["animators"].size())
	lines.append("Sprites: %d" % scan_result["sprites"].size())
	lines.append("AnimatedSprites: %d" % scan_result["animated_sprites"].size())
	lines.append("AnimationPlayers: %d" % scan_result["players"].size())
	lines.append("AnimationTrees: %d" % scan_result["trees"].size())
	lines.append("Skeletons: %d" % scan_result["skeletons"].size())
	return "\n".join(lines)
