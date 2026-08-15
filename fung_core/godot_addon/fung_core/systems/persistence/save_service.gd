class_name SaveService
extends RefCounted

var _logger: FungLogger


func _init(logger: FungLogger = null) -> void:
	_logger = logger


func save_json(path: String, data: Dictionary) -> Error:
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		var err := FileAccess.get_open_error()
		if _logger != null:
			_logger.error("SaveService", "Failed to open '%s' for writing: %s" % [path, error_string(err)])
		return err
	file.store_string(JSON.stringify(data, "  "))
	file.close()
	return OK


func load_json(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		if _logger != null:
			_logger.error("SaveService", "Failed to open '%s' for reading: %s" % [path, error_string(FileAccess.get_open_error())])
		return {}
	var text := file.get_as_text()
	file.close()
	var parsed = JSON.parse_string(text)
	if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
		if _logger != null:
			_logger.error("SaveService", "Failed to parse JSON from '%s'" % path)
		return {}
	return parsed
