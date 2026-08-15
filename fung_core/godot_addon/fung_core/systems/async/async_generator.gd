class_name AsyncGenerator
extends RefCounted

signal completed(result: Variant)
signal failed(error: String)

var _thread: Thread
var _cancelled := false
var _mutex := Mutex.new()


func run(callable: Callable) -> void:
	_cancelled = false
	_thread = Thread.new()
	_thread.start(_run_callable.bind(callable))


func cancel() -> void:
	# Arbitrary Callables can't be safely interrupted mid-run; this only stops a future run's signals, not an in-flight one.
	_mutex.lock()
	_cancelled = true
	_mutex.unlock()


# GDScript has no generic try/catch, so `callable` must return an Error-shaped result or handle its own errors internally.
func _run_callable(callable: Callable) -> void:
	if not callable.is_valid():
		_finish_failed("AsyncGenerator: callable is not valid")
		return

	var result: Variant = callable.call()
	_finish_completed(result)


func _finish_completed(result: Variant) -> void:
	_mutex.lock()
	var cancelled := _cancelled
	_mutex.unlock()
	if not cancelled:
		completed.emit.call_deferred(result)


func _finish_failed(message: String) -> void:
	_mutex.lock()
	var cancelled := _cancelled
	_mutex.unlock()
	if not cancelled:
		failed.emit.call_deferred(message)
