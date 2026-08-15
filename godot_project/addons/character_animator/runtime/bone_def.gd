class_name BoneDef
extends Resource
## A single bone definition inside a CharacterRig.
##
## parent_bone names the parent; empty string means the root. rest_*
## properties define the rest pose applied when the skeleton is built.

@export var bone_name: StringName = &""
@export var parent_bone: StringName = &""
@export var rest_position: Vector2 = Vector2.ZERO
@export var rest_rotation: float = 0.0
@export var rest_scale: Vector2 = Vector2.ONE
@export var z_index: int = 0
@export var sprite_texture: Texture2D = null
@export var sprite_offset: Vector2 = Vector2.ZERO
