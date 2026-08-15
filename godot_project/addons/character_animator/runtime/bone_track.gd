class_name BoneTrack
extends Resource
## One bone's keyframe track inside a BoneClip. Keys stay sorted by time.

@export var bone_name: StringName = &""
@export var keys: Array[BoneKey] = []


func add_key(key: BoneKey) -> void:
	if key == null:
		return
	for i in range(keys.size()):
		if keys[i].time > key.time:
			keys.insert(i, key)
			return
	keys.append(key)


func set_key(key: BoneKey) -> void:
	remove_key_at_time(key.time)
	add_key(key)


func remove_key_at(index: int) -> void:
	if index >= 0 and index < keys.size():
		keys.remove_at(index)


func remove_key_at_time(time: float) -> void:
	for i in range(keys.size() - 1, -1, -1):
		if is_equal_approx(keys[i].time, time):
			keys.remove_at(i)


func key_count() -> int:
	return keys.size()


func duration() -> float:
	if keys.is_empty():
		return 0.0
	return keys[keys.size() - 1].time


func sample(time: float) -> BoneKey:
	if keys.is_empty():
		return null
	if keys.size() == 1:
		return keys[0]
	if time <= keys[0].time:
		return keys[0]
	if time >= keys[keys.size() - 1].time:
		return keys[keys.size() - 1]
	var index := 0
	for i in range(keys.size()):
		if keys[i].time > time:
			index = i - 1
			break
	var a := keys[index]
	var b := keys[index + 1]
	var span := b.time - a.time
	var t := 0.0 if span <= 0.0 else (time - a.time) / span
	var out := BoneKey.new()
	out.time = time
	out.position = a.position.lerp(b.position, t)
	out.rotation = lerpf(a.rotation, b.rotation, t)
	out.scale = a.scale.lerp(b.scale, t)
	return out
