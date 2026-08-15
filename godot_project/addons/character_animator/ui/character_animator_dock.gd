@tool
extends VBoxContainer
## The plugin's editor dock: three tabs (Clips, Rig, Setup) driven by the
## current scene selection.

const ClipTabScript := preload("res://addons/character_animator/editor/clip_editor_tab.gd")
const RigTabScript := preload("res://addons/character_animator/editor/rig_editor_tab.gd")
const SetupTabScript := preload("res://addons/character_animator/editor/setup_tab.gd")

var editor_interface: EditorInterface

var _tabs: TabContainer
var _clip_tab: Control
var _rig_tab: Control
var _setup_tab: Control


func _ready() -> void:
	_tabs = TabContainer.new()
	_tabs.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_tabs)

	_clip_tab = ClipTabScript.new()
	_clip_tab.name = "Clips"
	_rig_tab = RigTabScript.new()
	_rig_tab.name = "Rig"
	_setup_tab = SetupTabScript.new()
	_setup_tab.name = "Setup"

	_tabs.add_child(_clip_tab)
	_tabs.add_child(_rig_tab)
	_tabs.add_child(_setup_tab)


func setup(editor: EditorInterface) -> void:
	editor_interface = editor
	_clip_tab.editor_interface = editor
	_rig_tab.editor_interface = editor
	_setup_tab.editor_interface = editor
	if editor != null:
		var selection := editor.get_selection()
		if selection != null and not selection.selection_changed.is_connected(refresh_from_selection):
			selection.selection_changed.connect(refresh_from_selection)
	refresh_from_selection()


func refresh_from_selection() -> void:
	_clip_tab.refresh_target()
	_rig_tab.refresh_target()
	_setup_tab.refresh_target()


func focus_setup() -> void:
	if _tabs != null:
		_tabs.current_tab = _tabs.get_tab_count() - 1


func focus_profile(profile: CharacterAnimationProfile) -> void:
	focus_setup()
	if _setup_tab != null and _setup_tab.has_method("load_profile"):
		_setup_tab.load_profile(profile)
