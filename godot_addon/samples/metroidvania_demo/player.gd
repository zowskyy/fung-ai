extends CharacterBody2D

# Real (if minimal) side-view platformer controller for the Fung Godot
# Toolkit's metroidvania_demo sample project: gravity, jump, left/right
# movement, using CharacterBody2D.move_and_slide() against the level's
# TileMapLayer collision. Not a game - just enough to demonstrate the
# addon's side-view/platformer-oriented recipes in a real physics context.
#
# Builds its own visual (ColorRect) and collision shape in code so this
# sample doesn't need a hand-authored player.tscn.
#
# IMPORTANT CAVEAT: this controller's collisions against terrain only work
# if tileset/fung_tileset.tres actually has a working physics layer +
# collision polygon on the wall tile. That .tres was hand-written without
# a Godot binary to verify it (see its own header comment and this
# project's README.md) - if the player falls straight through the level,
# start there, not here.
#
# UNVERIFIED: authored with no Godot binary available in this environment.
# Not run or tested by a real Godot engine - see repo root commit message.

const SPEED := 120.0
const JUMP_VELOCITY := -260.0
const GRAVITY := 900.0


func _ready() -> void:
	var shape := CollisionShape2D.new()
	var rect := RectangleShape2D.new()
	rect.size = Vector2(10.0, 14.0)
	shape.shape = rect
	add_child(shape)

	var visual := ColorRect.new()
	visual.size = Vector2(10.0, 14.0)
	visual.position = Vector2(-5.0, -7.0)
	visual.color = Color(0.3, 0.7, 0.95)
	add_child(visual)


func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y += GRAVITY * delta

	var direction := 0.0
	if Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A):
		direction -= 1.0
	if Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D):
		direction += 1.0
	velocity.x = direction * SPEED

	var jump_pressed: bool = (
		Input.is_key_pressed(KEY_SPACE)
		or Input.is_key_pressed(KEY_UP)
		or Input.is_key_pressed(KEY_W)
	)
	if is_on_floor() and jump_pressed:
		velocity.y = JUMP_VELOCITY

	move_and_slide()
