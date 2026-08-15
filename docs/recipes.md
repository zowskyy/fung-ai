# Built-in Recipes

Recipes are defined in `bridge/generation.py` as `RecipeConfig` entries in
the `RECIPES` dict. Each recipe fully determines a cellular-automaton run:
a Game-of-Life-style `rule_string` (`B<birth>/S<survive>`), an
`initial_density` (fraction of cells alive/wall at seeding time), a number
of CA `steps` to iterate, and `fitness_targets` (metric ranges used to score
each generated candidate — see `docs/bridge_protocol.md` for how `score` is
computed from these).

Generation is seed-deterministic: the same seed + recipe + map size always
produces the same grid (see `initialize_random()` / `step_ca()` in
`fung_ai_v2`).

This list reflects `RECIPES` as of this writing (`python3 -c "from
bridge.generation import RECIPES; print(list(RECIPES.keys()))"`). If new
recipes have been added since, re-run that command and update this file.

## `compact_roguelike_rooms`

> Roguelike with compact rooms and clear paths

| Field | Value |
|---|---|
| `rule_string` | `B3/S23` |
| `initial_density` | `0.35` |
| `steps` | `120` |
| `fitness_targets` | `walkable_ratio: (0.35, 0.55)`, `path_length: (40, 100)` |

`B3/S23` is the classic Conway's Life rule. At a moderate seed density and
120 iterations, this settles into pockets of open floor (rooms) connected
by narrower passages, with a moderate walkable-ratio target — a top-down,
room-and-corridor layout.

## `open_exploration`

> Open caverns for exploration

| Field | Value |
|---|---|
| `rule_string` | `B4/S3` |
| `initial_density` | `0.25` |
| `steps` | `80` |
| `fitness_targets` | `walkable_ratio: (0.50, 0.75)`, `path_length: (30, 80)` |

Lower starting density plus a higher birth threshold (a cell only turns to
wall with 4+ wall neighbors) biases the automaton toward eroding into large
connected open areas rather than isolated rooms — the highest
`walkable_ratio` target of the three built-in recipes, consistent with an
open-cavern layout.

## `dense_maze`

> Dense maze-like corridors

| Field | Value |
|---|---|
| `rule_string` | `B2/S23` |
| `initial_density` | `0.55` |
| `steps` | `100` |
| `fitness_targets` | `walkable_ratio: (0.20, 0.35)`, `path_length: (80, 150)` |

High starting density (55% wall) with a low birth threshold (`B2`) keeps
wall coverage dense, targeting the lowest `walkable_ratio` range of the
three recipes alongside the longest `path_length` target — consistent with
tight, winding maze-like corridors rather than open rooms.

## Notes for recipe authors

- `version` on `RecipeConfig` defaults to `"1.0.0"` if not set explicitly.
- `fitness_targets` is optional; a recipe with no targets gets a flat
  `score` of `0.75` for every candidate (see `_score_from_targets()` in
  `bridge/generation.py`).
- See `.github/ISSUE_TEMPLATE/recipe_submission.md` for the checklist to
  submit a new community recipe.
