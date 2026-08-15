class_name SpriteSheetFactory
extends RefCounted
## Generates placeholder 2D character art at runtime so demos, tests and the
## editor preview need no binary image assets.

const SKIN := Color(0.93, 0.78, 0.55)
const OUTLINE := Color(0.10, 0.08, 0.12)
const SHIRT := Color(0.22, 0.55, 0.85)
const PANTS := Color(0.30, 0.28, 0.62)


static func generate_character_sheet(frame_size := Vector2i(48, 48), columns := 8, rows := 4) -> ImageTexture:
	var image := Image.create_empty(frame_size.x * columns, frame_size.y * rows, false, Image.FORMAT_RGBA8)
	image.fill(Color(0.0, 0.0, 0.0, 0.0))
	for row in rows:
		for col in columns:
			var origin := Vector2i(col * frame_size.x, row * frame_size.y)
			_draw_pose(image, origin, frame_size, row, col)
	return ImageTexture.create_from_image(image)


static func solid_texture(size := Vector2i(24, 24), color := Color(1, 1, 1)) -> ImageTexture:
	var image := Image.create_empty(size.x, size.y, false, Image.FORMAT_RGBA8)
	image.fill(color)
	return ImageTexture.create_from_image(image)


static func _draw_pose(image: Image, origin: Vector2i, frame: Vector2i, row: int, col: int) -> void:
	var cx := origin.x + frame.x / 2
	var ground_y := origin.y + frame.y - 4
	var phase := float(col)
	var crouched := row == 3

	var shoulder := Vector2i(cx, origin.y + 20)
	var hip := Vector2i(cx, origin.y + 32)
	if crouched:
		shoulder = Vector2i(cx, origin.y + 26)
		hip = Vector2i(cx, origin.y + 33)

	# Head (outline then fill)
	var head := Vector2i(cx + int(sin(phase * 0.6) * 2.0), origin.y + 11)
	_fill_circle(image, head, 9, OUTLINE)
	_fill_circle(image, head, 7, SKIN)

	# Torso
	var torso := Rect2i(cx - 5, shoulder.y, 10, hip.y - shoulder.y)
	image.fill_rect(torso, SHIRT)
	image.fill_rect(Rect2i(cx - 5, shoulder.y, 10, 2), OUTLINE)

	# Arms swing opposite to the legs
	var arm_swing := int(sin(phase * 0.9) * 7.0)
	_draw_line(
		image,
		Vector2i(shoulder.x - 4, shoulder.y + 2),
		Vector2i(shoulder.x - 4 - arm_swing, shoulder.y + 11 + absi(arm_swing)),
		SKIN, 3)
	_draw_line(
		image,
		Vector2i(shoulder.x + 4, shoulder.y + 2),
		Vector2i(shoulder.x + 4 + arm_swing, shoulder.y + 11 + absi(arm_swing)),
		SKIN, 3)

	# Legs
	var leg_swing := int(sin(phase * 0.9 + PI) * 9.0)
	var left_foot := Vector2i(hip.x - 4 + leg_swing, ground_y)
	var right_foot := Vector2i(hip.x + 4 + leg_swing, ground_y)
	_draw_line(image, hip, left_foot, PANTS, 5)
	_draw_line(image, hip, right_foot, PANTS, 5)


static func _draw_line(image: Image, a: Vector2i, b: Vector2i, color: Color, width: int) -> void:
	var start := Vector2(a)
	var end := Vector2(b)
	var radius := maxi(1, width / 2)
	var dist := start.distance_to(end)
	if dist <= 0.001:
		_fill_circle(image, a, radius, color)
		return
	var dir := (end - start) / dist
	var steps := maxi(int(dist * 2.0), 1)
	for i in range(steps + 1):
		var point := start + dir * (dist * float(i) / float(steps))
		_fill_circle(image, Vector2i(point), radius, color)


static func _fill_circle(image: Image, center: Vector2i, radius: int, color: Color) -> void:
	var radius_sq := radius * radius
	for y in range(-radius, radius + 1):
		for x in range(-radius, radius + 1):
			if x * x + y * y <= radius_sq:
				image.set_pixel(center.x + x, center.y + y, color)
