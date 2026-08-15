# Fung Metroidvania Demo (sample project)

A minimal, side-view integration demo for the Fung Godot Toolkit addon,
with a real gravity + jump platformer controller instead of the top-down
free movement used by `roguelike_demo` and `exploration_demo`. **This is
not a game** - it exists to show the addon's generated output consumed by
a real, if trivial, playable scene.

## What it demonstrates

- A real candidate produced by the recipe `vertical_metroidvania_cavern`
  ("Tall winding cavern for vertical metroidvania-style traversal" - see
  `../../../docs/recipes.md`), at a tall `56x100` map size (narrow width,
  tall height - per the recipe docs, the "side view" framing comes from
  this orientation choice, not a different generation algorithm), seed 3.
- Decoding the `rle-v1` grid format and building a `TileMapLayer` from it
  at runtime, the same way `fung_export_service.gd`'s `_build_scene()`
  does when exporting from inside the editor (see `main.gd`).
- Spawning a real side-view `CharacterBody2D` controller (`player.gd`)
  with gravity and a jump, at the payload's `spawn_cell` position (placed
  on the top edge by the generator), with a visible marker at
  `exit_cell` (bottom edge).
- A debug label showing the recipe id and seed that produced this level.

## IMPORTANT: platforming collision is unverified

This is the one sample of the three where real physics collision against
the level terrain actually matters (a platformer needs the player to land
on and be blocked by walls, unlike the other two demos' free-roam
top-down movement).

**`fung_export_service.gd`'s `_build_scene()` - which this project's
`main.gd` deliberately mirrors - does not configure any tile collision
itself.** It only calls `TileMapLayer.set_cell()` to paint tile ids; any
collision the resulting level has comes entirely from the `TileSet`
resource it's pointed at. So the correctness of this demo's platforming
depends entirely on `tileset_builder.gd` actually building a `TileSet`
with a working physics layer and a collision polygon on the wall tile
(atlas coord `(1,0)`).

`tileset_builder.gd`'s `build(true)` attempts exactly that, using Godot
4.3's documented TileSet scripting API (`TileSet.add_physics_layer()`,
`TileSet.set_physics_layer_collision_layer()` /
`set_physics_layer_collision_mask()`, `TileData.add_collision_polygon()`,
`TileData.set_collision_polygon_points()`) rather than a hand-serialized
`.tres` resource file - chosen specifically because calling the real
scripting API is more likely to be correct than guessing the on-disk
resource text format by hand. **It has still never been run by a real
Godot engine**, because there is no Godot binary available anywhere in
the environment that authored it - see the header comment in
`tileset_builder.gd` for the full detail, including the one specific
API-naming risk it calls out (`Image.create()` vs `Image.create_empty()`
around the Godot 4.3 timeframe).

**If the player falls straight through the floor when you run this demo,
start there**: open a scene using this TileSet in the Godot editor (or
just read through `tileset_builder.gd`) and check whether the physics
layer and wall-tile collision polygon actually got created, and fix the
API calls if any signature has drifted. The floor/wall atlas layout itself
(`(0,0)` = floor, `(1,0)` = wall) is a separate, much lower-risk piece of
the same script and should still be correct regardless.

## How the data was produced

`data/result.json` and `data/candidates/candidate_001.json` are **real**
output - not hand-written. They were produced by actually running:

```
python3 -m bridge.fung_bridge --request <request.json> --response <job_dir>/result.json
```

from the repo root (`bridge/` and `fung_ai_v2/` importable), against the
request shown (with job-directory paths redacted to `<job_dir>/...`) in
`data/request.json` - `vertical_metroidvania_cavern`, seed 3,
`map_size_tiles: [56, 100]`, `generation_budget: "fast"`. `result.json`
was then trimmed down to just its first candidate to keep this sample
minimal. See `docs/bridge_protocol.md` in the repo root for the exact JSON
shapes.

## How to open and run

1. Open Godot **4.3+**, "Import" this folder (`metroidvania_demo/`) as a
   project - it does *not* need the `fung_godot` addon installed, since it
   only consumes a pre-generated JSON payload, not the live editor plugin.
2. Run `main.tscn` (F5 / the default main scene).
3. Move with **A/D** or **left/right arrows**, jump with **space**,
   **up**, or **W**.

## Art

There is no image asset in this project at all. `tileset_builder.gd`
builds a minimal 2-tile floor/wall `TileSet` **procedurally at runtime**
(a filled `Image` wrapped in an `ImageTexture`, plus the collision setup
described above) - no art tools were available to produce a placeholder
texture file, and this repo's root `.gitignore` excludes `*.png` outside
`research/**` anyway, so a committed placeholder PNG would have been
silently dropped from version control. Swap `tileset_builder.gd`'s
`build()` for one that loads a real `TileSet` resource/art asset when you
have one; the atlas layout it produces (floor at atlas coord `(0,0)`, wall
at `(1,0)`, source id `0`) matches what `fung_export_service.gd` expects
either way.

## Honesty note

None of this project's GDScript (`main.gd`, `player.gd`,
`tileset_builder.gd`) or its hand-written `.tscn` file have been opened or
run by a real Godot binary - there is no Godot executable available in the
environment that authored them. They are unverified until real CI
(`.github/workflows/godot_addon.yml`, which would need to be extended to
cover `godot_addon/samples/` to actually check this) or a human running a
real Godot editor confirms they work. Do not read "written" as "tested" -
and treat the collision setup described above as the least-verified part
of the entire addon.
