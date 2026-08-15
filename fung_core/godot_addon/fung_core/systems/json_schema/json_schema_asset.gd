class_name JsonSchemaAsset
extends Resource

@export var schema: Dictionary = {}

var _compiled: CompiledSchema = null


func _init(p_schema: Dictionary = {}) -> void:
	if p_schema:
		schema = p_schema


func get_compiled() -> CompiledSchema:
	if _compiled == null:
		_compile()
	return _compiled


func _compile() -> void:
	_compiled = CompiledSchema.new(schema)


func is_valid_instance(data: Variant) -> bool:
	var result := get_compiled().validate(data)
	return result.success


func validate(data: Variant) -> ValidationResult:
	return get_compiled().validate(data)
