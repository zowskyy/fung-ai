class_name BoneClip
extends Resource
## A named, time-based animation for a skeleton: one BoneTrack per animated
## bone. sample() fills a dictionary mapping bone name -> interpolated BoneKey.

@export var name: StringName = &""
@export var tracks: Array[BoneTrack] = []
@export var loop: bool = true


func duration() -> float:
	var longest := 1.0
	for track in tracks:
		if track != null:
			longest = maxf(longest, track.duration())
	return longest


func track_for(bone_name: StringName) -> BoneTrack:
	for track in tracks:
		if track != null and track.bone_name == bone_name:
			return track
	return null


func add_track(track: BoneTrack) -> bool:
	if track == null or track.bone_name == &"":
		return false
	if track_for(track.bone_name) != null:
		return false
	tracks.append(track)
	return true


func ensure_track(bone_name: StringName) -> BoneTrack:
	var track := track_for(bone_name)
	if track == null:
		track = BoneTrack.new()
		track.bone_name = bone_name
		add_track(track)
	return track


func remove_track(bone_name: StringName) -> void:
	for i in range(tracks.size() - 1, -1, -1):
		if tracks[i].bone_name == bone_name:
			tracks.remove_at(i)


func sample(time: float, out: Dictionary) -> void:
	for track in tracks:
		if track == null or track.keys.is_empty():
			continue
		var key := track.sample(time)
		if key != null:
			out[track.bone_name] = key
