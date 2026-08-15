@tool
class_name EndBeatRunner
extends BeatRunner


func start() -> void:
	completed.emit()
