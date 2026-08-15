---
name: Recipe submission
about: Propose a new built-in cave generation recipe
title: "[Recipe] "
labels: recipe
assignees: ''
---

Community recipe submissions should include everything below so
maintainers can verify the recipe is deterministic and produces the
gameplay shape you're claiming, without having to guess parameters. See
`docs/recipes.md` for the format of existing built-in recipes and
`bridge/generation.py`'s `RecipeConfig` for the exact fields.

## Recipe identity

- **`recipe_id`**: <!-- e.g. "winding_river_caves" -->
- **`version`**: <!-- e.g. "1.0.0" -->
- **One-line description**:

## Parameters

- **`rule_string`** (Game-of-Life style `B<birth>/S<survive>`):
- **`initial_density`** (0.0-1.0):
- **`steps`** (CA iteration count):

## `fitness_targets`

List each metric this recipe targets, with its `(min, max)` range (see
`docs/bridge_protocol.md` for what each metric means):

| Metric | Min | Max |
|---|---|---|
| `walkable_ratio` | | |
| `path_length` | | |

(add rows for `loop_count`, `branch_count`, `open_space_score` if targeted)

## Deterministic reproduction

A specific seed + map size that a maintainer can run to verify this
recipe's behavior, and the metric ranges you'd expect back:

- **Seed**:
- **Map size** (`map_size_tiles`, `[width, height]`):
- **Expected `walkable_ratio` range**:
- **Expected `path_length` range**:
- **Expected `score` range** (or "should satisfy all `fitness_targets`"):

## What kind of cave does this produce?

Describe the gameplay shape (room-based, open cavern, maze-like corridors,
etc.) and why the rule/density/steps combination produces it. Note this is
a headless engine — please describe this in terms of the grid/metrics
behavior you've observed, not a visual render.

## License / attribution

Confirm this submission is offered under the project's MIT license, and
credit yourself (or whoever should be credited) as you'd like it to appear
in `CHANGELOG.md` / `docs/recipes.md`.

- [ ] I confirm this recipe (parameters and any accompanying description)
      is submitted under the project's MIT license.
