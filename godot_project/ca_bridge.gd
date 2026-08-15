# ca_bridge.gd — Subprocess wrapper for the fung_ai_v2 CA engine.
#
# Usage:
#   var bridge = CaBridge.new()
#   var result = bridge.generate(rule="B3/S23", width=50, height=50, ticks=30, seed=42)
#   if result.has("grid"):
#       var grid = result["grid"]  # Array of Arrays of floats (0.0=wall, 1.0=floor)
#
# The bridge tries the refactored package CLI first:
#   python -m fung_ai_v2.cli generate ...
# and falls back to the legacy monolith:
#   python fungaiV2_extracted/fung_ai_v2.py generate ...
#
# OS.execute() blocks until the subprocess exits (no native timeout in Godot 4).
# For 20x20/5-tick calls this is well under 1s; larger grids may take a few
# seconds. Caller should invoke from a Thread if UI responsiveness matters.

extends RefCounted
class_name CaBridge

const PYTHON_EXE := "C:/Users/thewi/AppData/Local/Programs/Python/Python314/python.exe"
const PROJECT_ROOT := "C:/Users/thewi/OneDrive/Desktop/fung.us"

# Required keys that must be present in a valid CA engine JSON response.
const REQUIRED_KEYS := ["grid", "rule", "playable", "width", "height"]


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #

## Run the CA engine and return the parsed result Dictionary.
## Returns an empty Dictionary on any failure (error already push_error'd).
func generate(
		rule: String = "B3/S23",
		width: int = 50,
		height: int = 50,
		ticks: int = 30,
		seed: int = 42,
		lat: float = 0.0,
		lon: float = 0.0,
		use_env: bool = false) -> Dictionary:

	var cli_path := _find_cli()
	if cli_path.is_empty():
		push_error("CaBridge: could not locate CA engine CLI (checked package and legacy paths)")
		return {}

	# Build the argument list.
	var args := PackedStringArray()

	if cli_path.ends_with(".py"):
		# Legacy monolith: python path/to/fung_ai_v2.py generate ...
		args.append(cli_path)
	else:
		# Package module: python -m fung_ai_v2.cli generate ...
		args.append("-m")
		args.append(cli_path)

	args.append("generate")
	args.append("--rule")
	args.append(rule)
	args.append("--width")
	args.append(str(width))
	args.append("--height")
	args.append(str(height))
	args.append("--ticks")
	args.append(str(ticks))
	args.append("--seed")
	args.append(str(seed))

	if use_env and (lat != 0.0 or lon != 0.0):
		args.append("--lat")
		args.append(str(lat))
		args.append("--lon")
		args.append(str(lon))

	return _run_python(args)


## Return the Python executable path.
func get_python_exe() -> String:
	return PYTHON_EXE


## Return the path that will be used for the CA CLI on the next generate() call.
func get_ca_script_path() -> String:
	return _find_cli()


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

## Locate the CA CLI.  Prefers the refactored package; falls back to legacy.
## Returns:
##   "fung_ai_v2.cli"  — package module name (used with -m flag)
##   "<abs_path>.py"   — legacy script absolute path
##   ""                — nothing found
func _find_cli() -> String:
	# --- try package-style: fung_ai_v2/cli.py ---------------------------------
	var pkg_cli := PROJECT_ROOT.path_join("fung_ai_v2/cli.py")
	if FileAccess.file_exists(pkg_cli):
		return "fung_ai_v2.cli"

	# --- fall back to legacy monolith ------------------------------------------
	var legacy := PROJECT_ROOT.path_join("fungaiV2_extracted/fung_ai_v2.py")
	if FileAccess.file_exists(legacy):
		return legacy

	return ""


## Run the Python executable with the given argument list.
## Captures stdout and returns the first JSON object found in it.
## Returns {} on subprocess error or JSON parse failure.
func _run_python(args: PackedStringArray) -> Dictionary:
	var output := []   # OS.execute fills this with stdout as a single String

	# OS.execute blocks until the child exits.  The working directory is
	# PROJECT_ROOT so that `python -m fung_ai_v2.cli` can find its package.
	var exit_code := OS.execute(PYTHON_EXE, args, output, false, false)

	if exit_code != 0:
		push_error("CaBridge: python exited with code %d. args=%s" % [exit_code, str(args)])
		if output.size() > 0:
			push_error("CaBridge: stdout was: %s" % str(output[0]).left(500))
		return {}

	if output.is_empty() or str(output[0]).strip_edges().is_empty():
		push_error("CaBridge: python produced no output")
		return {}

	# The CA engine may print [env] diagnostic lines to stdout before the JSON.
	# Find the first line that starts with '{'.
	var raw_out := str(output[0])
	var json_start := raw_out.find("{")
	if json_start < 0:
		push_error("CaBridge: no JSON object found in python output: %s" % raw_out.left(300))
		return {}

	var json_text := raw_out.substr(json_start)

	var parsed = JSON.parse_string(json_text)
	if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
		push_error("CaBridge: JSON parse failed. raw=%s" % json_text.left(300))
		return {}

	var result: Dictionary = parsed

	# Validate required keys.
	for key in REQUIRED_KEYS:
		if not result.has(key):
			push_error("CaBridge: CA engine response missing required key '%s'" % key)
			return {}

	# Sanity-check grid shape.
	var grid: Array = result["grid"]
	if grid.is_empty():
		push_error("CaBridge: CA engine returned empty grid")
		return {}
	if not grid[0] is Array:
		push_error("CaBridge: grid[0] is not an Array (expected Array of Arrays)")
		return {}

	return result
