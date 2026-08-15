@tool
extends Node

class_name FungManifest

## Reads and writes reproducibility manifests: one small JSON file per
## exported scene recording the recipe/seed/profile/metrics that produced
## it, so a level can be identified, audited, or regenerated later.
##
## Manifests live at res://generated/fung/manifests/<scene_name>.fung.json.

const FORMAT_VERSION: int = 1
const FUNG_VERSION_DEFAULT: String = "0.1.0"
# No recipe- or export-profile-versioning system exists yet anywhere in this
# codebase; these are placeholder defaults until one is built. Callers may
# override them via candidate_data if/when that system exists.
const RECIPE_VERSION_DEFAULT: String = "1.0.0"
const EXPORT_PROFILE_VERSION_DEFAULT: String = "1.0.0"

var _manifest_root: String = "res://generated/fung/manifests/"


# Write a reproducibility manifest for an exported candidate.
#   scene_name: base name for the manifest file (usually the candidate_id
#     or export scene name, no extension) - also used to look it up later.
#   candidate_data: a candidate dict (as found in result.json's
#     "candidates" list) merged by the caller with whatever extra context
#     it has in scope: recipe_id, fung_version (generator_version),
#     map_size_tiles (from the candidate payload's grid_size), and
#     optionally tile_size_px / generation_inputs / recipe_version /
#     export_profile_version. Missing fields fall back to sensible
#     defaults rather than failing the write.
#   export_profile: export profile name used for this export.
#   scene_path: path (res:// or user://) the exported scene was written to.
# Returns true if the manifest was written successfully.
func write_manifest(
	scene_name: String,
	candidate_data: Dictionary,
	export_profile: String,
	scene_path: String,
) -> bool:
	if scene_name.is_empty():
		push_error("FungManifest.write_manifest: scene_name is required")
		return false

	DirAccess.make_dir_recursive_absolute(_manifest_root)

	var manifest: Dictionary = {
		"format_version": FORMAT_VERSION,
		"fung_version": candidate_data.get("fung_version", FUNG_VERSION_DEFAULT),
		"recipe_id": candidate_data.get("recipe_id", ""),
		"recipe_version": candidate_data.get("recipe_version", RECIPE_VERSION_DEFAULT),
		"export_profile": export_profile,
		"export_profile_version": candidate_data.get(
			"export_profile_version", EXPORT_PROFILE_VERSION_DEFAULT
		),
		"seed": candidate_data.get("seed", 0),
		"created_utc": _now_utc_iso8601(),
		"map_size_tiles": candidate_data.get("map_size_tiles", [96, 96]),
		"tile_size_px": candidate_data.get("tile_size_px", [16, 16]),
		"quality_metrics": candidate_data.get("metrics", {}),
		"generation_inputs": candidate_data.get("generation_inputs", {}),
		"files": {
			"scene": scene_path,
			"preview": candidate_data.get("preview_path", ""),
		},
	}

	var manifest_path: String = _get_manifest_path(scene_name)
	var file: FileAccess = FileAccess.open(manifest_path, FileAccess.WRITE)
	if file == null:
		push_error("Failed to open manifest for writing: %s" % manifest_path)
		return false

	file.store_string(JSON.stringify(manifest, "\t"))
	file.flush()
	return true


# Read a single manifest by scene name. Returns {} if missing or invalid.
func read_manifest(scene_name: String) -> Dictionary:
	return _read_json_safe(_get_manifest_path(scene_name))


# Scan the manifests directory and return every manifest found, newest
# first (sorted by created_utc). Returns [] if the directory doesn't exist
# yet (e.g. nothing has been exported).
func list_manifests() -> Array[Dictionary]:
	var results: Array[Dictionary] = []

	var dir: DirAccess = DirAccess.open(_manifest_root)
	if dir == null:
		return results

	dir.list_dir_begin()
	var file_name: String = dir.get_next()
	while file_name != "":
		if not dir.current_is_dir() and file_name.ends_with(".fung.json"):
			var manifest: Dictionary = _read_json_safe(_manifest_root.path_join(file_name))
			if not manifest.is_empty():
				results.append(manifest)
		file_name = dir.get_next()
	dir.list_dir_end()

	results.sort_custom(_compare_created_utc_desc)
	return results


func _compare_created_utc_desc(a: Dictionary, b: Dictionary) -> bool:
	return String(a.get("created_utc", "")) > String(b.get("created_utc", ""))


func _get_manifest_path(scene_name: String) -> String:
	return _manifest_root.path_join(scene_name + ".fung.json")


# ISO-8601-ish UTC timestamp, e.g. "2026-01-01T00:00:00Z".
# Time.get_datetime_string_from_system(utc=true) returns the current
# datetime already converted to UTC, but without any timezone marker
# (per Godot 4.3 docs) - so append "Z" explicitly to mark it as UTC,
# matching the sample manifest format from the Library tab spec.
func _now_utc_iso8601() -> String:
	return Time.get_datetime_string_from_system(true) + "Z"


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
