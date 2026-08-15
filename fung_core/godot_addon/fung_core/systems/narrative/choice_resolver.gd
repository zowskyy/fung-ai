class_name ChoiceResolver
extends RefCounted


func resolve(beat: Dictionary, option_id: String) -> String:
	var options: Array = beat.get("options", [])
	for option: Dictionary in options:
		if option.get("id", "") == option_id:
			return option.get("next", "")
	return ""
