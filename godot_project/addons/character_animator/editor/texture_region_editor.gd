@tool
class_name TextureRegionEditor
extends Control
## Interactive sprite-sheet region picker. Drag with the left mouse button to
## define a Rect2 in texture pixels; the mouse wheel zooms.

signal region_selected(region: Rect2)

var texture: Texture2D = null:
	set(value):
		texture = value
		queue_redraw()

var region: Rect2 = Rect2():
	set(value):
		region = value
		queue_redraw()

const MIN_ZOOM := 0.25
const MAX_ZOOM := 8.0

var zoom := 1.0
var _dragging := false
var _drag_start := Vector2.ZERO

var disabled := false:
	set(value):
		disabled = value
		mouse_filter = Control.MOUSE_FILTER_IGNORE if value else Control.MOUSE_FILTER_STOP
		queue_redraw()


func _init() -> void:
	custom_minimum_size = Vector2(220, 180)
	mouse_filter = Control.MOUSE_FILTER_STOP


func set_zoom(value: float) -> void:
	zoom = clampf(value, MIN_ZOOM, MAX_ZOOM)
	queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if disabled or texture == null:
		return
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				_dragging = true
				_drag_start = _to_texture(mb.position)
				region = Rect2(_drag_start, Vector2.ZERO)
				accept_event()
			elif _dragging:
				_dragging = false
				region_selected.emit(region)
				accept_event()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_UP:
			set_zoom(zoom * 1.2)
			accept_event()
		elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			set_zoom(zoom / 1.2)
			accept_event()
	if _dragging and event is InputEventMouseMotion:
		var mm := event as InputEventMouseMotion
		region = Rect2(_drag_start, _to_texture(mm.position) - _drag_start).abs()
		accept_event()


func _to_texture(position: Vector2) -> Vector2:
	if texture == null:
		return position
	return (position / zoom).clamp(Vector2.ZERO, texture.get_size())


func _draw() -> void:
	if texture == null:
		draw_string(ThemeDB.fallback_font, Vector2(8, 16), "No texture",
			HORIZONTAL_ALIGNMENT_LEFT, -1, 12, Color(0.6, 0.6, 0.6))
		return
	var draw_size := texture.get_size() * zoom
	draw_texture_rect(texture, Rect2(Vector2.ZERO, draw_size), false)
	if region.size.x > 0.0 and region.size.y > 0.0:
		var rect := Rect2(region.position * zoom, region.size * zoom)
		draw_rect(rect, Color(0.0, 0.0, 0.0, 0.35), true)
		draw_rect(rect, Color(0.4, 0.95, 0.5), false, 1.5)
		draw_string(ThemeDB.fallback_font, rect.position + Vector2(4, -6),
			"%dx%d" % [int(region.size.x), int(region.size.y)],
			HORIZONTAL_ALIGNMENT_LEFT, -1, 11, Color(0.95, 0.95, 0.95))
