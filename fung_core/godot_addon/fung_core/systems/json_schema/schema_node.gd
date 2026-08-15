class_name SchemaNode
extends Node

@export var schema: Variant = null

signal validation_failed(result: ValidationResult)


func _init(p_schema: Variant = null) -> void:
	if p_schema:
		schema = p_schema


func validate(data: Variant) -> ValidationResult:
	if schema == null:
		var result := ValidationResult.new()
		result.success = false
		result.add_error("No schema asset assigned to SchemaNode")
		return result

	if schema is JsonSchemaAsset:
		return schema.validate(data)

	# Support inline dictionary schemas by wrapping them
	if schema is Dictionary:
		var asset := JsonSchemaAsset.new(schema)
		return asset.validate(data)

	var result := ValidationResult.new()
	result.success = false
	result.add_error("Schema must be a JsonSchemaAsset or Dictionary")
	return result


func is_valid(data: Variant) -> bool:
	var result := validate(data)
	if not result.success:
		validation_failed.emit(result)
	return result.success
