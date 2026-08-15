@tool
class_name SceneCameraAdapter
extends Node

## Generic contract for camera logic driven by CameraBeats. Base provides a
## functional no-op transition (immediately signals completion so a plan can
## run without a real camera rig). Game-specific camera rigs subclass and
## override request_mode to blend a Camera3D/Camera2D rig.

signal camera_transitioned(mode_id: StringName)
signal camera_failed(mode_id: StringName, reason: StringName)

@export var default_blend_seconds := 0.25
@export var focus_target: Node3D


func request_mode(mode_id: StringName, focus_target_node: Node3D, blend_seconds: float) -> void:
	if focus_target_node != null:
		focus_target = focus_target_node
	camera_transitioned.emit(mode_id)


func cancel() -> void:
	camera_transitioned.emit(&"")  # noqa
