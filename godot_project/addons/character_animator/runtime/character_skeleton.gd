class_name CharacterSkeleton
extends Node2D
## Builds a Skeleton2D/Bone2D hierarchy from a CharacterRig and applies
## animated bone poses (typically driven by a SkeletonAnimator).

@export var rig: CharacterRig = null

var skeleton: Skeleton2D = null
var bone_nodes: Dictionary = {}


func _ready() -> void:
	if rig != null:
		build_from_rig(rig)


func has_bone(bone_name: StringName) -> bool:
	return bone_nodes.has(bone_name)


func get_bone_node(bone_name: StringName) -> Bone2D:
	return bone_nodes.get(bone_name) as Bone2D


func bone_names() -> PackedStringArray:
	var names := PackedStringArray()
	for bone_name in bone_nodes:
		names.append(bone_name)
	return names


func build_from_rig(target_rig: CharacterRig) -> void:
	if skeleton != null:
		skeleton.queue_free()
	skeleton = Skeleton2D.new()
	skeleton.name = "Skeleton2D"
	add_child(skeleton)
	bone_nodes.clear()
	var seen := {}
	for bone in target_rig.bones:
		if bone != null and bone.bone_name != &"":
			if not seen.has(bone.bone_name):
				seen[bone.bone_name] = true
	var ordered := target_rig.topologically_ordered_bones()
	for bone in ordered:
		if bone == null:
			continue
		var parent_node: Node = skeleton
		if bone.parent_bone != &"" and bone.parent_bone != target_rig.root_bone and seen.has(bone.parent_bone):
			parent_node = bone_nodes.get(bone.parent_bone, skeleton)
		if bone_nodes.has(bone.bone_name):
			continue
		bone_nodes[bone.bone_name] = _create_bone_node(bone, parent_node)


func _create_bone_node(bone: BoneDef, parent_node: Node) -> Bone2D:
	var node := Bone2D.new()
	node.name = String(bone.bone_name)
	node.position = bone.rest_position
	node.rotation = bone.rest_rotation
	node.scale = bone.rest_scale
	var length := bone.rest_position.length()
	node.default_length = maxf(length, 0.001)
	node.z_index = bone.z_index
	if bone.sprite_texture != null:
		var sprite := Sprite2D.new()
		sprite.name = "Part"
		sprite.texture = bone.sprite_texture
		sprite.position = bone.sprite_offset
		node.add_child(sprite)
	parent_node.add_child(node)
	return node


func apply_pose(bone_name: StringName, position: Vector2, rotation: float, scale: Vector2) -> void:
	var bone := get_bone_node(bone_name)
	if bone == null:
		return
	bone.position = position
	bone.rotation = rotation
	bone.scale = scale


func reset_to_rest() -> void:
	for bone_name in bone_nodes:
		var bone: Bone2D = bone_nodes[bone_name]
		var def: BoneDef = null
		if rig != null:
			def = rig.get_bone(bone_name)
		if def != null:
			bone.position = def.rest_position
			bone.rotation = def.rest_rotation
			bone.scale = def.rest_scale
		else:
			bone.position = Vector2.ZERO
			bone.rotation = 0.0
			bone.scale = Vector2.ONE
