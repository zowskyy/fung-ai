@tool
class_name CharacterAnimationProfileInspector
extends EditorInspectorPlugin
## Adds a small header and a shortcut button when a CharacterAnimationProfile
## is inspected, so profiles can be sent straight to the plugin dock.

var _open_callback: Callable = Callable()


func set_open_callback(callback: Callable) -> void:
	_open_callback = callback


func _can_handle(object: Object) -> bool:
	return object is CharacterAnimationProfile


func _parse_begin(object: Object) -> void:
	var profile := object as CharacterAnimationProfile
	if profile == null:
		return
	var label := Label.new()
	label.text = "Character Animator profile (%d semantic clips)" % profile.animation_names().size()
	add_custom_control(label)
	var button := Button.new()
	button.text = "Open in Character Animator dock"
	button.pressed.connect(func():
		if _open_callback.is_valid():
			_open_callback.call(profile))
	add_custom_control(button)
