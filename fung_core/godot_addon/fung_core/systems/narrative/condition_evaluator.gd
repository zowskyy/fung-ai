class_name ConditionEvaluator
extends RefCounted


func evaluate(when: Dictionary, flags: Dictionary) -> bool:
	if when.is_empty():
		return true
	return flags.get(when.get("flag", ""), null) == when.get("equals", true)
