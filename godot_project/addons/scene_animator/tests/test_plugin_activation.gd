class_name TestPluginActivation
extends RefCounted

## Plugin activation contract. Validates plugin wiring statically, then boots
## the full editor headlessly (`--headless --editor --quit-after 3`) and asserts
## the process exits 0 with no scene_animator-attributable script errors.
##
## The editor subprocess is the authoritative plugin lifecycle check: it is the
## startup mode where EditorPlugin._enter_tree()/add_control_to_dock() are
## actually exercised. --headless --import is deliberately not used for this,
## because import-only startup does not establish the editor dock tree.

const ADDON := "res://addons/scene_animator/"
const PLUGIN_CFG := "res://addons/scene_animator/plugin.cfg"
const PLUGIN_SCRIPT := "res://addons/scene_animator/plugin.gd"
const DOCK_SCRIPT := "res://addons/scene_animator/editor/scene_plan_dock.gd"
const INSPECTOR_SCRIPT := "res://addons/scene_animator/editor/inspectors/scene_plan_inspector.gd"
const VALIDATOR_SCRIPT := "res://addons/scene_animator/editor/validators/scene_plan_validator.gd"

var _ctx: SceneAnimatorTestContext


func run() -> SceneAnimatorTestResult:
	var result := SceneAnimatorTestResult.new()
	result.suite_name = &"test_plugin_activation"
	_ctx = SceneAnimatorTestContext.new(result)
	var started_ms := Time.get_ticks_msec()

	_test_plugin_config()
	_test_plugin_script()
	_test_referenced_editor_scripts()
	await _test_editor_boot()

	result.duration_ms = Time.get_ticks_msec() - started_ms
	return result


func _test_plugin_config() -> void:
	var cfg := ConfigFile.new()
	var err := cfg.load(PLUGIN_CFG)
	_ctx.equals(err, OK, &"plugin.cfg_loads", "plugin.cfg must parse as a ConfigFile.")
	if err != OK:
		return
	var script_name: String = cfg.get_value("plugin", "script", "")
	_ctx.equals(script_name, "plugin.gd", &"plugin.cfg_script_field", "plugin.cfg must declare script=plugin.gd.")
	var name: String = cfg.get_value("plugin", "name", "")
	_ctx.is_true(name != "", &"plugin.cfg_name", "plugin.cfg must declare a non-empty name.")
	var version: String = cfg.get_value("plugin", "version", "")
	_ctx.is_true(version != "", &"plugin.cfg_version", "plugin.cfg must declare a version.")
	_ctx.is_true(FileAccess.file_exists(PLUGIN_SCRIPT), &"plugin.cfg_script_exists", "plugin.cfg script target must exist.")


func _test_plugin_script() -> void:
	var script := load(PLUGIN_SCRIPT)
	_ctx.is_true(script != null, &"plugin.gd_loads", "plugin.gd must load.")
	if script == null:
		return
	_ctx.equals(script.get_instance_base_type(), &"EditorPlugin", &"plugin.gd_extends_editor", "plugin.gd must extend EditorPlugin.")
	var method_names := _method_names(script)
	_ctx.is_true(method_names.has(&"_enter_tree"), &"plugin.gd_enter_tree", "plugin.gd must implement _enter_tree.")
	_ctx.is_true(method_names.has(&"_exit_tree"), &"plugin.gd_exit_tree", "plugin.gd must implement _exit_tree.")


func _test_referenced_editor_scripts() -> void:
	var dock := load(DOCK_SCRIPT)
	_ctx.is_true(dock != null, &"plugin.dock_loads", "Dock script must load.")
	if dock != null:
		_ctx.equals(dock.get_instance_base_type(), &"PanelContainer", &"plugin.dock_extends_control", "Dock must extend a Control type.")
	var inspector := load(INSPECTOR_SCRIPT)
	_ctx.is_true(inspector != null, &"plugin.inspector_loads", "Inspector script must load.")
	if inspector != null:
		_ctx.equals(inspector.get_instance_base_type(), &"EditorInspectorPlugin", &"plugin.inspector_extends", "Inspector must extend EditorInspectorPlugin.")
	_ctx.is_true(load(VALIDATOR_SCRIPT) != null, &"plugin.validator_loads", "Validator script must load.")


func _test_editor_boot() -> void:
	var godot_bin := OS.get_environment(&"GODOT_BIN")
	if godot_bin == "":
		godot_bin = "godot"
	var project_dir := ProjectSettings.globalize_path(&"res://")
	var args := PackedStringArray([
		"--headless",
		"--editor",
		"--path", project_dir,
		"--quit-after", "3",
	])
	var output: Array = []
	var exit_code := OS.execute(godot_bin, args, output, true)

	var message := "Editor headless boot with the plugin enabled must exit 0. Got %d." % exit_code
	_ctx.equals(exit_code, 0, &"plugin.editor_boot_exit", message)

	var errors := _filter_scene_animator_errors(output)
	_ctx.is_true(errors.is_empty(), &"plugin.editor_boot_no_errors", "Editor boot must not emit scene_animator-attributable errors.", {
		"errors": errors,
	})


func _method_names(script: Script) -> Array[StringName]:
	var names: Array[StringName] = []
	for method: Dictionary in script.get_script_method_list():
		names.append(method["name"])
	return names


func _filter_scene_animator_errors(output: Array) -> Array[String]:
	var errors: Array[String] = []
	for raw: Variant in output:
		var line := String(raw)
		if not line.contains("scene_animator"):
			continue
		if line.contains("SCRIPT ERROR") or line.contains("ERROR") or line.contains("Scene Animator:"):
			errors.append(line)
	return errors
