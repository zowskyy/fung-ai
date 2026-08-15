@tool
class_name UndoService
extends RefCounted
## Thin wrapper around the editor's UndoRedo so every scene mutation made by
## the plugin is a single reversible step. Falls back to direct mutation when
## no EditorInterface is available (e.g. runtime use in tests).

var editor_interface: EditorInterface = null


func _init(editor: EditorInterface = null) -> void:
	editor_interface = editor


func add_node(parent: Node, node: Node, scene_root: Node) -> void:
	var undo := _undo_redo()
	if undo == null:
		parent.add_child(node)
		node.owner = scene_root
		return
	undo.create_action("Add %s" % node.get_class())
	undo.add_do_method(parent.add_child.bind(node))
	undo.add_do_method(node.set_owner.bind(scene_root))
	undo.add_undo_method(parent.remove_child.bind(node))
	undo.commit_action()


func remove_node(parent: Node, node: Node) -> void:
	var undo := _undo_redo()
	if undo == null:
		parent.remove_child(node)
		node.queue_free()
		return
	undo.create_action("Remove %s" % node.get_class())
	undo.add_do_method(parent.remove_child.bind(node))
	undo.add_undo_method(parent.add_child.bind(node))
	undo.commit_action()


func set_property(object: Object, property: String, new_value: Variant, old_value: Variant, action_name := "Set Property") -> void:
	var undo := _undo_redo()
	if undo == null:
		object.set(property, new_value)
		return
	undo.create_action(action_name)
	undo.add_do_property(object, property, new_value)
	undo.add_undo_property(object, property, old_value)
	undo.commit_action()


func _undo_redo() -> UndoRedo:
	if editor_interface == null:
		return null
	return editor_interface.get_undo_redo()
