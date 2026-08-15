@tool
extends Node

class_name FungBackendClient

## Manages job lifecycle: process invocation, status polling, result importing.

signal generation_started(request_id: String)
signal generation_progress(request_id: String, progress: float, stage: String, message: String)
signal generation_completed(request_id: String, success: bool, error_message: String)
signal generation_cancelled(request_id: String)

enum JobState {
	IDLE,
	PREPARING,
	LAUNCHING,
	RUNNING,
	IMPORTING_RESULT,
	READY_TO_EXPORT,
	EXPORTING,
	EXPORTED,
	FAILED,
	CANCELLED,
}

var _job_state: JobState = JobState.IDLE
var _current_request_id: String = ""
var _job_dir: String = ""
var _process_pid: int = -1
var _polling_timer: Timer = null
var _python_executable: String = ""


func _ready() -> void:
	if Engine.is_editor_hint():
		_setup_polling()


func _setup_polling() -> void:
	"""Create and configure the polling timer."""
	_polling_timer = Timer.new()
	_polling_timer.wait_time = 0.15  # 150ms polling interval
	_polling_timer.timeout.connect(_poll_status)
	add_child(_polling_timer)


func start_generation(
	request_id: String,
	request_path: String,
	response_path: String,
	job_dir: String,
) -> bool:
	"""Start a generation job. Returns true if subprocess launched successfully."""
	if _job_state != JobState.IDLE:
		push_error("Backend client not idle (state=%s)" % JobState.keys()[_job_state])
		return false

	_current_request_id = request_id
	_job_dir = job_dir
	_set_state(JobState.PREPARING)

	# Resolve Python executable
	_python_executable = _resolve_python_executable()
	if _python_executable.is_empty():
		_set_state(JobState.FAILED)
		generation_completed.emit(request_id, false, "Python executable not found")
		return false

	# Launch subprocess
	_set_state(JobState.LAUNCHING)
	var args: PackedStringArray = PackedStringArray([
		"-m",
		"bridge.fung_bridge",
		"--request",
		request_path,
		"--response",
		response_path,
	])

	_process_pid = OS.create_process(_python_executable, args, false)
	if _process_pid <= 0:
		_set_state(JobState.FAILED)
		generation_completed.emit(request_id, false, "Failed to launch Python subprocess")
		return false

	_set_state(JobState.RUNNING)
	generation_started.emit(request_id)

	# Start polling
	if _polling_timer:
		_polling_timer.start()

	return true


func cancel_generation() -> void:
	"""Cooperatively cancel the current generation job."""
	if _job_state != JobState.RUNNING:
		return

	var cancel_path: String = _job_dir.path_join("cancel.request")
	var file: FileAccess = FileAccess.open(cancel_path, FileAccess.WRITE)
	if file:
		file.store_string("")
		_set_state(JobState.CANCELLED)
		generation_cancelled.emit(_current_request_id)
	else:
		push_error("Failed to write cancel.request to %s" % cancel_path)


func _poll_status() -> void:
	"""Poll status.json and handle state transitions."""
	if _job_state != JobState.RUNNING:
		if _polling_timer:
			_polling_timer.stop()
		return

	var status_path: String = _job_dir.path_join("status.json")
	if not ResourceLoader.exists(status_path):
		return

	var status_data: Dictionary = _read_json_safe(status_path)
	if status_data.is_empty():
		return

	var state: String = status_data.get("state", "")
	var progress: float = status_data.get("progress", 0.0)
	var stage: String = status_data.get("stage", "")
	var message: String = status_data.get("message", "")

	generation_progress.emit(_current_request_id, progress, stage, message)

	# Handle state transitions
	if state == "completed":
		_set_state(JobState.IMPORTING_RESULT)
		if _polling_timer:
			_polling_timer.stop()
		generation_completed.emit(_current_request_id, true, "")
		_reset_for_next_job()

	elif state == "failed" or state == "error":
		_set_state(JobState.FAILED)
		if _polling_timer:
			_polling_timer.stop()
		var error_msg: String = status_data.get("message", "Unknown error")
		generation_completed.emit(_current_request_id, false, error_msg)
		_reset_for_next_job()

	elif state == "cancelled":
		_set_state(JobState.CANCELLED)
		if _polling_timer:
			_polling_timer.stop()
		generation_cancelled.emit(_current_request_id)
		_reset_for_next_job()


func _resolve_python_executable() -> String:
	"""Resolve Python executable path (priority: env var, then 'python3', then 'python')."""
	# Check FUNG_PYTHON environment variable
	var python_env: String = OS.get_environment("FUNG_PYTHON")
	if not python_env.is_empty():
		if FileAccess.file_exists(python_env):
			return python_env

	# Try standard commands
	for cmd: String in ["python3", "python"]:
		var result: int = OS.execute_to_string(cmd, ["-c", "import sys; print(1)"])
		if result == 0:
			return cmd

	return ""


func _read_json_safe(path: String) -> Dictionary:
	"""Safely read and parse JSON file, returns empty dict on error."""
	if not FileAccess.file_exists(path):
		return {}

	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}

	var text: String = file.get_as_text()
	var json: JSON = JSON.new()
	var error: Error = json.parse(text)

	if error != OK:
		return {}

	var data: Variant = json.data
	if data is Dictionary:
		return data

	return {}


func _set_state(new_state: JobState) -> void:
	"""Transition to a new state."""
	if new_state != _job_state:
		_job_state = new_state


func _reset_for_next_job() -> void:
	"""Reset internal state for next generation job."""
	_current_request_id = ""
	_job_dir = ""
	_process_pid = -1
	_set_state(JobState.IDLE)


func get_job_state() -> JobState:
	"""Get current job state."""
	return _job_state


func is_idle() -> bool:
	"""Check if backend is idle and ready for new jobs."""
	return _job_state == JobState.IDLE
