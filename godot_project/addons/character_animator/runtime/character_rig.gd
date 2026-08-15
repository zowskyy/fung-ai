class_name CharacterRig
extends Resource
## The bone layout for a CharacterSkeleton. Bones are created in parent order;
## validate() catches duplicate names and dangling parents.

@export var bones: Array[BoneDef] = []
@export var root_bone: StringName = &""


func bone_names() -> PackedStringArray:
	var out := PackedStringArray()
	for bone in bones:
		if bone != null:
			out.append(bone.bone_name)
	return out


func get_bone(bone_name: StringName) -> BoneDef:
	for bone in bones:
		if bone != null and bone.bone_name == bone_name:
			return bone
	return null


func has_bone(bone_name: StringName) -> bool:
	return get_bone(bone_name) != null


func add_bone(bone: BoneDef) -> bool:
	if bone == null or bone.bone_name == &"":
		return false
	if has_bone(bone.bone_name):
		return false
	bones.append(bone)
	if root_bone == &"":
		root_bone = bone.bone_name
	return true


func remove_bone(bone_name: StringName) -> void:
	for i in range(bones.size() - 1, -1, -1):
		if bones[i].bone_name == bone_name:
			bones.remove_at(i)
	if root_bone == bone_name:
		root_bone = &""
		if not bones.is_empty():
			root_bone = bones[0].bone_name


func validate() -> bool:
	var seen := {}
	for bone in bones:
		if bone == null or bone.bone_name == &"":
			return false
		if seen.has(bone.bone_name):
			return false
		seen[bone.bone_name] = true
	for bone in bones:
		if bone.parent_bone != &"" and not seen.has(bone.parent_bone):
			return false
	return true


func topologically_ordered_bones() -> Array:
	var ordered: Array = []
	var pending := bones.duplicate()
	var progressed := true
	while not pending.is_empty() and progressed:
		progressed = false
		for i in range(pending.size() - 1, -1, -1):
			var bone := pending[i] as BoneDef
			if bone == null:
				pending.remove_at(i)
				continue
			if bone.parent_bone != &"" and bone.parent_bone != root_bone:
				var parent_found := false
				for existing in ordered:
					if existing.bone_name == bone.parent_bone:
						parent_found = true
						break
				if not parent_found:
					continue
			ordered.append(bone)
			pending.remove_at(i)
			progressed = true
	for bone in pending:
		if bone != null:
			ordered.append(bone)
	return ordered
