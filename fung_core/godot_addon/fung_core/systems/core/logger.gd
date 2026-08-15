class_name FungLogger
extends RefCounted

enum Level {DEBUG, INFO, WARN, ERROR}

const _LEVEL_NAMES := {
	Level.DEBUG: "DEBUG",
	Level.INFO: "INFO",
	Level.WARN: "WARN",
	Level.ERROR: "ERROR",
}


func log(level: Level, tag: String, message: String) -> void:
	var formatted := "[%s] [%s] %s" % [_LEVEL_NAMES[level], tag, message]
	match level:
		Level.WARN:
			push_warning(formatted)
		Level.ERROR:
			push_error(formatted)
		_:
			print(formatted)


func debug(tag: String, message: String) -> void:
	log(Level.DEBUG, tag, message)


func info(tag: String, message: String) -> void:
	log(Level.INFO, tag, message)


func warn(tag: String, message: String) -> void:
	log(Level.WARN, tag, message)


func error(tag: String, message: String) -> void:
	log(Level.ERROR, tag, message)
