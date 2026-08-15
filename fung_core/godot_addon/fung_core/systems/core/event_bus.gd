class_name EventBus
extends RefCounted

signal event_emitted(event_name: String, payload: Dictionary)

var _listeners: Dictionary = {}


func subscribe(event_name: String, handler: Callable) -> void:
	if not _listeners.has(event_name):
		_listeners[event_name] = []
	var handlers: Array = _listeners[event_name]
	if not handlers.has(handler):
		handlers.append(handler)


func unsubscribe(event_name: String, handler: Callable) -> void:
	if not _listeners.has(event_name):
		return
	var handlers: Array = _listeners[event_name]
	handlers.erase(handler)
	if handlers.is_empty():
		_listeners.erase(event_name)


func emit_event(event_name: String, payload: Dictionary = {}) -> void:
	if _listeners.has(event_name):
		for handler: Callable in (_listeners[event_name] as Array).duplicate():
			if handler.is_valid():
				handler.call(payload)
	event_emitted.emit(event_name, payload)
