extends RefCounted

# Builds a minimal, fully procedural placeholder floor/wall TileSet at
# runtime - no image file involved. This repo's root .gitignore excludes
# *.png everywhere outside research/**, so a checked-in placeholder PNG
# (the original plan) would have been silently dropped from version
# control; procedural generation also matches this project's stated asset
# policy ("original, CC0, or procedurally generated").
#
# Produces exactly the atlas layout fung_export_service.gd's
# _build_scene() expects: source id 0, floor at atlas coord (0,0), wall at
# atlas coord (1,0).
#
# Unlike roguelike_demo/exploration_demo's copy of this script, build()
# here also adds a physics layer and a square collision polygon on the
# wall tile, since metroidvania_demo's player.gd is a real gravity/jump
# platformer that needs to actually land on and be blocked by walls.
#
# UNVERIFIED - and this is the single least-verified piece of this entire
# sample: this relies on Image.create_empty() / TileSetAtlasSource /
# TileSet.add_physics_layer() / TileData.add_collision_polygon() /
# TileData.set_collision_polygon_points() scripting APIs exactly as they
# exist in Godot 4.3, written with no Godot binary available anywhere to
# confirm the method names/signatures. (Image.create() was renamed to
# create_empty() around the 4.3 timeframe - if this build still expects
# the old name, this will fail at runtime.) If the player falls straight
# through the floor when this demo is actually run, start here - see this
# project's README.md for the full caveat.

const TILE_PX := 16
const FLOOR_COLOR := Color(0.769, 0.698, 0.580)  # warm light gray
const WALL_COLOR := Color(0.239, 0.2, 0.169)      # dark brown-gray


func build(with_wall_collision: bool = false) -> TileSet:
	var image: Image = Image.create_empty(TILE_PX * 2, TILE_PX, false, Image.FORMAT_RGBA8)
	image.fill_rect(Rect2i(0, 0, TILE_PX, TILE_PX), FLOOR_COLOR)
	image.fill_rect(Rect2i(TILE_PX, 0, TILE_PX, TILE_PX), WALL_COLOR)
	var texture: ImageTexture = ImageTexture.create_from_image(image)

	var atlas_source: TileSetAtlasSource = TileSetAtlasSource.new()
	atlas_source.texture = texture
	atlas_source.texture_region_size = Vector2i(TILE_PX, TILE_PX)
	atlas_source.create_tile(Vector2i(0, 0))
	atlas_source.create_tile(Vector2i(1, 0))

	var tile_set: TileSet = TileSet.new()
	tile_set.tile_size = Vector2i(TILE_PX, TILE_PX)
	tile_set.add_source(atlas_source, 0)

	if with_wall_collision:
		tile_set.add_physics_layer()
		tile_set.set_physics_layer_collision_layer(0, 1)
		tile_set.set_physics_layer_collision_mask(0, 1)

		var wall_data: TileData = atlas_source.get_tile_data(Vector2i(1, 0), 0)
		if wall_data:
			var half: float = TILE_PX / 2.0
			var points: PackedVector2Array = PackedVector2Array([
				Vector2(-half, -half),
				Vector2(half, -half),
				Vector2(half, half),
				Vector2(-half, half),
			])
			wall_data.add_collision_polygon(0)
			wall_data.set_collision_polygon_points(0, 0, points)

	return tile_set
