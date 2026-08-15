extends CharacterBody2D

# Minimal top-down player controller for the Fung Godot Toolkit's
# roguelike_demo sample project. This exists only to demonstrate spawning
# a controllable character at the exported PlayerSpawn position - it is
# not a game. No combat, no health, no interaction with Exit/gameplay
# markers.
#
# Builds its own visual (ColorRect) and collision shape in code so this
# sample doesn't need a hand-authored player.tscn - see the "no ext_resource
# id mismatches" caution in this repo's other GDScript.
#
# No physics dependency beyond CharacterBody2D.move_and_slide() - this
# controller does not rely on the TileMapLayer having any tile collision
# configured (unlike metroidvania_demo/player.gd).
#
# UNVERIFIED: authored with no Godot binary available in this environment.
# Not run or tested by a real Godot engine - see repo root commit message.

const SPEED := 140.0


func _ready() -> void:
	var shape := CollisionShape2D.new()
	var circle := CircleShape2D.new()
	circle.radius = 6.0
	shape.shape = circle
	add_child(shape)

	var visual := ColorRect.new()
	visual.size = Vector2(12, 12)
	visual.position = Vector2(-6, -6)
	visual.color = Color(0.95, 0.85, 0.2)
	add_child(visual)


func _physics_process(_delta: float) -> void:
	var input_vector := Vector2.ZERO
	if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A):
		input_vector.x -= 1.0
	if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
		input_vector.x += 1.0
	if Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W):
		input_vector.y -= 1.0
	if Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S):
		input_vector.y += 1.0

	if input_vector != Vector2.ZERO:
		velocity = input_vector.normalized() * SPEED
	else:
		velocity = Vector2.ZERO

	move_and_slide()
