class_name FrameSplitter
extends RefCounted


func process_over_frames(tree: SceneTree, items: Array, per_frame: int, callback: Callable) -> void:
	var chunk_size := maxi(per_frame, 1)
	var index := 0
	while index < items.size():
		var chunk_end := mini(index + chunk_size, items.size())
		for i in range(index, chunk_end):
			callback.call(items[i])
		index = chunk_end
		if index < items.size():
			await tree.process_frame
