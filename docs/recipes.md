# Built-in Recipes

Recipes are defined in `bridge/generation.py` as `RecipeConfig` entries in
the `RECIPES` dict. Each recipe fully determines a cellular-automaton run:
a Game-of-Life-style `rule_string` (`B<birth>/S<survive>`), an
`initial_density` (fraction of cells alive/wall at seeding time), a number
of CA `steps` to iterate, and `fitness_targets` (metric ranges used to
score each generated candidate — see `docs/bridge_protocol.md` for how
`score` is computed from these).

Generation is seed-deterministic: the same seed + recipe + map size always
produces the same grid (see `initialize_random()` / `step_ca()` in
`fung_ai_v2`).

This list reflects `RECIPES` as of this writing (`python3 -c "from
bridge.generation import RECIPES; print(list(RECIPES.keys()))"` — 16
recipes). If more have been added since, re-run that command and update
this file.

Per the source comments in `bridge/generation.py`, every recipe's
`fitness_targets` here is empirically calibrated, not aspirational: each
`(rule_string, initial_density, steps)` combination was run across 30
seeds at its intended map size (fixtures under
`tests/fixtures/requests/<recipe_id>.json`, asserted by
`tests/test_recipes.py`), plus a spot-check across seeds 0-4 at 48x48
(`TestGenerateCandidateGrid.test_all_builtin_recipes_can_generate` in
`tests/test_generation.py`). The ranges are observed min/max with a
margin, not a guess — an earlier version of these three recipes had
targets that were never checked against real output and were off by a
wide margin (e.g. `compact_roguelike_rooms` claimed `walkable_ratio`
0.35-0.55 but actually produced ~0.90).

## Top-down caves

| Recipe | `rule_string` | Density | Steps | `walkable_ratio` | `path_length` |
|---|---|---|---|---|---|
| `compact_roguelike_rooms` | `B2/S23` | 0.45 | 8 | 0.55-0.75 | 85-175 |
| `open_exploration` | `B3/S23` | 0.30 | 15 | 0.72-0.90 | 65-135 |
| `dense_maze` | `B1/S12` | 0.45 | 30 | 0.55-0.70 | 75-140 |
| `branching_delve` | `B36/S238` | 0.40 | 8 | 0.62-0.80 | 80-165 |
| `flooded_network` | `B368/S245` | 0.30 | 30 | 0.65-0.88 | 75-165 |
| `crystal_caverns` | `B4/S45678` | 0.45 | 8 | 0.68-0.92 | 65-130 |
| `lava_tubes` | `B25/S4` | 0.40 | 30 | 0.65-0.80 | 80-140 |
| `fungal_underground` | `B368/S245` | 0.30 | 15 | 0.58-0.80 | 80-190 |
| `sewer_labyrinth` | `B35/S236` | 0.25 | 8 | 0.53-0.75 | 85-190 |
| `boss_arena_loops` | `B5678/S45678` | 0.45 | 30 | 0.60-0.87 | 70-140 |

- **`compact_roguelike_rooms`** (v1.1.0) — "Roguelike-style rooms connected
  by branching corridors."
- **`open_exploration`** (v1.1.0) — "Open caverns for exploration."
- **`dense_maze`** (v1.1.0) — "Dense maze-like corridors with the tightest
  chokepoints of any recipe."
- **`branching_delve`** — "Winding descent with frequent branching
  junctions."
- **`flooded_network`** — "Interconnected open chambers with abundant
  loops, like a flooded cave network."
- **`crystal_caverns`** — "Large faceted open chambers with high
  visibility."
- **`lava_tubes`** — "Winding tube-like corridors of consistently moderate
  width."
- **`fungal_underground`** — "Organic clustered pockets and irregular
  chambers."
- **`sewer_labyrinth`** — "Tight looping corridors with long winding
  paths."
- **`boss_arena_loops`** — "Open arena chambers with many loops and short
  paths, suited for boss encounters."

## Side-view / platformer-oriented caves

These use the exact same 2D CA engine as the top-down recipes above — per
the source comment in `bridge/generation.py`, the "side view" framing comes
from pairing the recipe with a tall (narrow width, tall height) or wide
`map_size_tiles` at request time, not from a different generation
algorithm. Spawn/exit are always placed on the top/bottom edges regardless
of orientation (see `_find_spawn_exit()` in `bridge/generation.py`).

| Recipe | `rule_string` | Density | Steps | `walkable_ratio` | `path_length` |
|---|---|---|---|---|---|
| `vertical_metroidvania_cavern` | `B36/S23` | 0.45 | 15 | 0.67-0.85 | 90-160 |
| `layered_mining_shafts` | `B234/S` | 0.30 | 5 | 0.60-0.77 | 100-265 |
| `wide_platforming_grotto` | `B4/S45678` | 0.40 | 5 | 0.78-0.97 | 50-100 |
| `hazardous_descent` | `B3/S45678` | 0.50 | 8 | 0.63-0.85 | 85-185 |
| `ice_climb` | `B36/S23` | 0.30 | 5 | 0.62-0.80 | 90-170 |
| `secret_tunnel_network` | `B4678/S35678` | 0.30 | 3 | 0.85-0.98 | 80-125 |

- **`vertical_metroidvania_cavern`** — "Tall winding cavern for vertical
  metroidvania-style traversal."
- **`layered_mining_shafts`** — "Long branching vertical mining shafts and
  connecting tunnels" (the widest `path_length` target of any recipe,
  100-265).
- **`wide_platforming_grotto`** — "Wide, highly open grotto suited for
  horizontal platforming" (the highest `walkable_ratio` target among the
  general-purpose recipes, 0.78-0.97).
- **`hazardous_descent`** — "Tall open cavern with a long, hazard-strewn
  descent."
- **`ice_climb`** — "Tall winding ascent with moderate branching."
- **`secret_tunnel_network`** — "Dense, highly-connected tunnel network
  riddled with secret branches" (the highest `walkable_ratio` target of
  any recipe, 0.85-0.98, and the fewest CA `steps`, 3).

## Notes for recipe authors

- `version` on `RecipeConfig` defaults to `"1.0.0"` if not set explicitly;
  the three original recipes (`compact_roguelike_rooms`,
  `open_exploration`, `dense_maze`) are at `"1.1.0"` after their
  `fitness_targets` were recalibrated against real output.
- `fitness_targets` is optional; a recipe with no targets gets a flat
  `score` of `0.75` for every candidate (see `_score_from_targets()` in
  `bridge/generation.py`).
- Before adding or retuning a recipe, run the same empirical calibration
  described above rather than hand-guessing ranges — see
  `tests/test_recipes.py` and `tests/fixtures/requests/` for the pattern.
- See `.github/ISSUE_TEMPLATE/recipe_submission.md` for the checklist to
  submit a new community recipe.
