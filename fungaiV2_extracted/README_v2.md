
# Fung-AI v2.0: Game-Design-Aware Quality-Diversity Cave Generator

## Overview

Fung-AI v2.0 evolves Conway-Life-style cellular automaton rules (B/S notation) into
2D cave/dungeon layouts using MAP-Elites, a quality-diversity (QD) optimization
algorithm, and exports the result to a Godot-4-compatible scene. The archive
organizes generated caves along axes that matter for game design — coverage, path
topology (linear/branching/open), and chokepoint density — rather than abstract CA
statistics, so you can query the archive for "give me your best branching cave" and
get something usable.

An earlier iteration of this project explored a landscape-adaptive multi-emitter
driver (switching between MAP-Elites, CMA-MAE, and Dominated Novelty Search based on
detected fitness-landscape type). Measured against the game-design-aware fitness in
this repo, that extra machinery gave no real benefit over plain MAP-Elites — see
"Measured Results" below — so it was removed. What ships now is the simpler,
verified-to-work version: MAP-Elites as the primary algorithm, Random Search kept
only as a baseline for comparison.

---

## What's Included

### Complete Implementation  
- **fung_ai_v2.py** — Full working Python codebase
  - CARule encoding/decoding (B/S notation)
  - CA simulation engine (Moore neighborhood)
  - Game-design-aware fitness function and behavior descriptors (see below)
  - GridArchive with CMA-MAE-style annealing thresholds
  - MAP-Elites emitter
  - `Standard_MAP_Elites` (primary algorithm) and `RandomSearch` (baseline)
  - GodotExporter for engine integration
  - CLI interface (generate, benchmark, compare, export, query)

---

## Fitness & Descriptors (Game-Design-Aware)

`evaluate_ca_rule()` and `compute_descriptors()` score and place caves using signals
that map to actual level-design concerns, computed from the passable (non-wall) cell
region of the final CA grid:

- **Coverage** — fraction of the grid that is wall. Fitness rewards coverage near
  ~35% (cave-like), not maximum coverage — an all-wall or all-empty grid still
  scores near the extinction floor.
- **Path topology score** (descriptor axis 2, 0-1) — approximated from the average
  number of passable Moore-neighborhood cells per passable cell (no `skimage`
  dependency; it's not installed in this environment, so this is a lightweight
  stand-in for skeleton-based branch counting). Bucketed via `classify_topology()`
  into `linear` (<0.33), `branching` (0.33-0.66), `open` (>0.66).
- **Chokepoint density** (descriptor axis 3, 0-1) — fraction of passable cells with
  <=2 passable neighbors, i.e. narrow corridors/doorways.
- **Pacing proxy** — variance of a 5x5 sliding-window passable-density map, a stand-in
  for alternating tight corridors and open rooms.
- **Interestingness** — pattern entropy (local 3x3 configuration variety) blended
  with the pacing variance.

The archive is 3-dimensional: `[coverage, path_topology_score, chokepoint_density]`,
each binned 0-1 over 10 bins.

Fitness (for grids at or above the 5% minimum-coverage gate — below that, extinction
is capped near 0.015 and cannot win):

```
fitness = 0.30 * coverage_quality      # peaks at ~35% coverage
        + 0.30 * path_exists           # top-to-bottom traversability
        + 0.15 * chokepoint_component  # rewards some, not too many, narrow passages
        + 0.10 * pacing_component
        + 0.15 * interestingness
```

---

## Quick Start

```bash
# Generate a cave with a specific CA rule
python fung_ai_v2.py generate --rule B3/S23 --width 100 --height 100 --ticks 50

# Run benchmark with MAP-Elites (default)
python fung_ai_v2.py benchmark --algorithm map_elites --evals 10000

# Compare MAP-Elites vs Random Search
python fung_ai_v2.py compare --evals 10000

# Export to Godot
python fung_ai_v2.py export --input cave.json --output godot_scene.json

# Query the archive for the best cave of a given style
python fung_ai_v2.py query --style branching --algorithm map_elites --evals 10000
```

`query` runs the chosen algorithm (`map_elites` or `random`) for the given evaluation
budget, buckets every archive elite by `classify_topology()`, and prints the
highest-fitness match for `--style linear|branching|open` as JSON (rule string,
fitness, descriptors, the generated grid, and a `playable` flag). If no elite of that
style was discovered, it reports `"found": false` rather than guessing.

---

## Measured Results (not aspirational)

These are actual `python fung_ai_v2.py compare --evals N` runs against the
game-design-aware fitness/descriptors in this repo, seed 42, default 20x20 grid.

**`--evals 2000`:**

| Algorithm | Coverage | QD-Score | Max Fitness | Success@10k |
|-----------|----------|----------|--------------|-------------|
| Random Search | 11.9% | 34.7 | 0.639 | 0.004 |
| MAP-Elites | 15.1% | 44.3 | 0.694 | 0.004 |

**`--evals 10000`:**

| Algorithm | Coverage | QD-Score | Max Fitness | Success@10k |
|-----------|----------|----------|--------------|-------------|
| Random Search | 16.4% | 47.7 | 0.717 | 0.001 |
| MAP-Elites | 17.7% | 53.1 | 0.707 | 0.001 |

Honest read: MAP-Elites gives a modest, consistent edge over Random Search in both
coverage and QD-score at both budgets tested — not dramatic, but real and repeatable.
An earlier version of this project also benchmarked a landscape-adaptive multi-emitter
algorithm (AAALE) alongside these two; it showed no consistent advantage over plain
MAP-Elites once fitness was reworked to be game-design-aware (it was sometimes the
weakest of the three), so it was removed rather than kept as unproven complexity.
Re-run `compare` yourself at your target budget and grid size before trusting these
numbers for a different configuration.

---

## License

Open source. See Fung-AI v1.0 shippable package for setup.py and full project structure.
