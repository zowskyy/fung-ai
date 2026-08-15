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
# UNVERIFIED: this relies on Image.create_empty() / TileSetAtlasSource /
# ImageTexture.create_from_image() scripting APIs as they exist in Godot
# 4.3 - written with no Godot binary available to confirm the exact method
# names/signatures still match (Image.create() was renamed to
# create_empty() around the 4.3 timeframe; if this project's Godot build
# still expects the old name, or the signature differs, this will fail at
# runtime). See this project's README.md.

const TILE_PX := 16
const FLOOR_COLOR := Color(0.769, 0.698, 0.580)  # warm light gray
const WALL_COLOR := Color(0.239, 0.2, 0.169)      # dark brown-gray


func build() -> TileSet:
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

	return tile_set
