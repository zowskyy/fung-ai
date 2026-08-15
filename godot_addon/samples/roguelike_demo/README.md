# Fung Roguelike Demo (sample project)

A minimal, top-down integration demo for the Fung Godot Toolkit addon.
**This is not a game** — it exists to show the addon's generated output
(a `TileMapLayer` + spawn/exit/gameplay markers) consumed by a real, if
trivial, playable scene.

## What it demonstrates

- A real candidate produced by the recipe `compact_roguelike_rooms`
  ("Roguelike-style rooms connected by branching corridors" — see
  `../../../docs/recipes.md`), at a 48x48 map size, seed 42.
- Decoding the `rle-v1` grid format and building a `TileMapLayer` from it
  at runtime, the same way `fung_export_service.gd`'s `_build_scene()`
  does when exporting from inside the editor (see `main.gd`).
- Spawning a simple top-down `CharacterBody2D` player at the payload's
  `spawn_cell` position, with a visible marker at `exit_cell`.
- A debug label showing the recipe id and seed that produced this level.

## How the data was produced

`data/result.json` and `data/candidates/candidate_001.json` are **real**
output — not hand-written. They were produced by actually running:

```
python3 -m bridge.fung_bridge --request <request.json> --response <job_dir>/result.json
```

from the repo root (`bridge/` and `fung_ai_v2/` importable), against the
request shown (with job-directory paths redacted to `<job_dir>/...`) in
`data/request.json` — `compact_roguelike_rooms`, seed 42, `map_size_tiles:
[48, 48]`, `generation_budget: "fast"`. `result.json` was then trimmed
down to just its first candidate to keep this sample minimal. See
`docs/bridge_protocol.md` in the repo root for the exact JSON shapes.

## How to open and run

1. Open Godot **4.3+**, "Import" this folder (`roguelike_demo/`) as a
   project — it does *not* need the `fung_godot` addon installed, since it
   only consumes a pre-generated JSON payload, not the live editor plugin.
2. Run `main.tscn` (F5 / the default main scene).
3. Move with **WASD** or **arrow keys**.

## Art

There is no image asset in this project at all. `tileset_builder.gd`
builds a minimal 2-tile floor/wall `TileSet` **procedurally at runtime**
(a filled `Image` wrapped in an `ImageTexture`) — no art tools were
available to produce a placeholder texture file, and this repo's root
`.gitignore` excludes `*.png` outside `research/**` anyway, so a
committed placeholder PNG would have been silently dropped from version
control. Swap `tileset_builder.gd`'s `build()` for one that loads a real
`TileSet` resource/art asset when you have one; the atlas layout it
produces (floor at atlas coord `(0,0)`, wall at `(1,0)`, source id `0`)
matches what `fung_export_service.gd` expects either way.

## Honesty note

None of this project's GDScript (`main.gd`, `player.gd`,
`tileset_builder.gd`) or its hand-written `.tscn` file have been opened or
run by a real Godot binary — there is no Godot executable available in the
environment that authored them. `tileset_builder.gd` in particular relies
on `Image`/`TileSetAtlasSource`/`ImageTexture` scripting APIs exactly as
they exist in Godot 4.3, unconfirmed. They are unverified until real CI
(`.github/workflows/godot_addon.yml`, which would need to be extended to
cover `godot_addon/samples/` to actually check this) or a human running a
real Godot editor confirms they work. Do not read "written" as "tested."
