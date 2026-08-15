class_name FungProjectSettings
extends RefCounted

var _values: Dictionary = {}


func _init(overrides: Dictionary = {}) -> void:
	_values = {
		"contracts_dir": "res://addons/fung_core/contracts",
		"default_budgets": {
			"world_generation_ms": 100,
			"frame_time_ms": 16.6,
		},
	}
	for key: String in overrides:
		_values[key] = overrides[key]


func get_contracts_dir() -> String:
	return _values["contracts_dir"]


func get_default_budgets() -> Dictionary:
	return _values["default_budgets"]
