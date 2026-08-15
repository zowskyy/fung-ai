"""Generation orchestration: coordinate fung_ai_v2 engine for recipes."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy import ndimage

from fung_ai_v2 import (
    CARule,
    compute_descriptors,
    has_path,
    initialize_random,
    step_ca,
)


@dataclass
class RecipeConfig:
    """Configuration for a recipe."""

    id: str
    version: str = "1.0.0"
    description: str = ""
    rule_string: str = "B3/S23"
    initial_density: float = 0.3
    steps: int = 100
    fitness_targets: dict[str, tuple[float, float]] | None = None


# Built-in recipes for v0.1.
#
# fitness_targets below are calibrated against REAL generate_candidate_grid()
# output, not aspiration: each recipe's (rule_string, initial_density, steps)
# combo was run across 30 seeds at its intended map size (see the recipe's
# fixture in tests/fixtures/requests/<id>.json and tests/test_recipes.py,
# which asserts the fixture seed's metrics fall inside these ranges) plus a
# spot-check across seeds 0-4 at 48x48 (the size used by
# TestGenerateCandidateGrid.test_all_builtin_recipes_can_generate in
# tests/test_generation.py). Targets are the observed min/max with a margin
# on each side, not a hoped-for range. If you add or retune a recipe, run the
# same empirical calibration before writing its targets -- an earlier version
# of compact_roguelike_rooms (and dense_maze/open_exploration) had
# fitness_targets that were never checked against real output and were
# wrong by a wide margin (e.g. compact_roguelike_rooms claimed
# walkable_ratio 0.35-0.55 but actually produced ~0.90).
RECIPES: dict[str, RecipeConfig] = {
    # --- Top-down caves ---
    "compact_roguelike_rooms": RecipeConfig(
        id="compact_roguelike_rooms",
        version="1.1.0",
        description="Roguelike-style rooms connected by branching corridors",
        rule_string="B2/S23",
        initial_density=0.45,
        steps=8,
        fitness_targets={
            "walkable_ratio": (0.55, 0.75),
            "path_length": (85, 175),
        },
    ),
    "open_exploration": RecipeConfig(
        id="open_exploration",
        version="1.1.0",
        description="Open caverns for exploration",
        rule_string="B3/S23",
        initial_density=0.30,
        steps=15,
        fitness_targets={
            "walkable_ratio": (0.72, 0.90),
            "path_length": (65, 135),
        },
    ),
    "dense_maze": RecipeConfig(
        id="dense_maze",
        version="1.1.0",
        description="Dense maze-like corridors with the tightest chokepoints of any recipe",
        rule_string="B1/S12",
        initial_density=0.45,
        steps=30,
        fitness_targets={
            "walkable_ratio": (0.55, 0.70),
            "path_length": (75, 140),
        },
    ),
    "branching_delve": RecipeConfig(
        id="branching_delve",
        description="Winding descent with frequent branching junctions",
        rule_string="B36/S238",
        initial_density=0.40,
        steps=8,
        fitness_targets={
            "walkable_ratio": (0.62, 0.80),
            "path_length": (80, 165),
        },
    ),
    "flooded_network": RecipeConfig(
        id="flooded_network",
        description="Interconnected open chambers with abundant loops, like a flooded cave network",
        rule_string="B368/S245",
        initial_density=0.30,
        steps=30,
        fitness_targets={
            "walkable_ratio": (0.65, 0.88),
            "path_length": (75, 165),
        },
    ),
    "crystal_caverns": RecipeConfig(
        id="crystal_caverns",
        description="Large faceted open chambers with high visibility",
        rule_string="B4/S45678",
        initial_density=0.45,
        steps=8,
        fitness_targets={
            "walkable_ratio": (0.68, 0.92),
            "path_length": (65, 130),
        },
    ),
    "lava_tubes": RecipeConfig(
        id="lava_tubes",
        description="Winding tube-like corridors of consistently moderate width",
        rule_string="B25/S4",
        initial_density=0.40,
        steps=30,
        fitness_targets={
            "walkable_ratio": (0.65, 0.80),
            "path_length": (80, 140),
        },
    ),
    "fungal_underground": RecipeConfig(
        id="fungal_underground",
        description="Organic clustered pockets and irregular chambers",
        rule_string="B368/S245",
        initial_density=0.30,
        steps=15,
        fitness_targets={
            "walkable_ratio": (0.58, 0.80),
            "path_length": (80, 190),
        },
    ),
    "sewer_labyrinth": RecipeConfig(
        id="sewer_labyrinth",
        description="Tight looping corridors with long winding paths",
        rule_string="B35/S236",
        initial_density=0.25,
        steps=8,
        fitness_targets={
            "walkable_ratio": (0.53, 0.75),
            "path_length": (85, 190),
        },
    ),
    "boss_arena_loops": RecipeConfig(
        id="boss_arena_loops",
        description="Open arena chambers with many loops and short paths, for boss encounters",
        rule_string="B5678/S45678",
        initial_density=0.45,
        steps=30,
        fitness_targets={
            "walkable_ratio": (0.60, 0.87),
            "path_length": (70, 140),
        },
    ),
    # --- Side-view / platformer-oriented caves ---
    # These use the same 2D CA engine as the top-down recipes; the "side
    # view" orientation comes from pairing the rule with a tall (narrow
    # width, tall height) or wide map_size_tiles at request time, since
    # spawn/exit are always placed on the top/bottom edges.
    "vertical_metroidvania_cavern": RecipeConfig(
        id="vertical_metroidvania_cavern",
        description="Tall winding cavern for vertical metroidvania-style traversal",
        rule_string="B36/S23",
        initial_density=0.45,
        steps=15,
        fitness_targets={
            "walkable_ratio": (0.67, 0.85),
            "path_length": (90, 160),
        },
    ),
    "layered_mining_shafts": RecipeConfig(
        id="layered_mining_shafts",
        description="Long branching vertical mining shafts and connecting tunnels",
        rule_string="B234/S",
        initial_density=0.30,
        steps=5,
        fitness_targets={
            "walkable_ratio": (0.60, 0.77),
            "path_length": (100, 265),
        },
    ),
    "wide_platforming_grotto": RecipeConfig(
        id="wide_platforming_grotto",
        description="Wide, highly open grotto suited for horizontal platforming",
        rule_string="B4/S45678",
        initial_density=0.40,
        steps=5,
        fitness_targets={
            "walkable_ratio": (0.78, 0.97),
            "path_length": (50, 100),
        },
    ),
    "hazardous_descent": RecipeConfig(
        id="hazardous_descent",
        description="Tall open cavern with a long, hazard-strewn descent",
        rule_string="B3/S45678",
        initial_density=0.50,
        steps=8,
        fitness_targets={
            "walkable_ratio": (0.63, 0.85),
            "path_length": (85, 185),
        },
    ),
    "ice_climb": RecipeConfig(
        id="ice_climb",
        description="Tall winding ascent with moderate branching",
        rule_string="B36/S23",
        initial_density=0.30,
        steps=5,
        fitness_targets={
            "walkable_ratio": (0.62, 0.80),
            "path_length": (90, 170),
        },
    ),
    "secret_tunnel_network": RecipeConfig(
        id="secret_tunnel_network",
        description="Dense, highly-connected tunnel network riddled with secret branches",
        rule_string="B4678/S35678",
        initial_density=0.30,
        steps=3,
        fitness_targets={
            "walkable_ratio": (0.85, 0.98),
            "path_length": (80, 125),
        },
    ),
}


@dataclass
class CandidateGrid:
    """A generated grid plus its derived spawn/exit cells."""

    grid: np.ndarray
    spawn_cell: tuple[int, int]
    exit_cell: tuple[int, int]
    markers: dict[str, list[tuple[int, int]]] = field(default_factory=dict)


def generate_candidate_grid(
    seed: int,
    map_size: tuple[int, int],
    recipe: RecipeConfig,
    progress_callback: Callable[[float, str], None] | None = None,
) -> CandidateGrid | None:
    """Generate a single candidate cave using CA engine.

    Returns a CandidateGrid (grid: 1=wall, 0=floor, plus spawn/exit) or
    None if the candidate has no valid top-to-bottom path.
    """
    width, height = map_size
    rule = CARule.from_string(recipe.rule_string)

    grid = initialize_random((height, width), seed, recipe.initial_density)

    if progress_callback:
        progress_callback(0.1, "Initialized")

    for step in range(recipe.steps):
        grid = step_ca(grid, rule)
        if progress_callback and step % 10 == 0:
            p = 0.1 + (step / recipe.steps) * 0.7
            progress_callback(p, f"Step {step}/{recipe.steps}")

    if progress_callback:
        progress_callback(0.85, "Validating")

    # has_path returns the fraction of the bottom row covered by a component
    # that also touches the top row; any value > 0 proves at least one
    # top-to-bottom path exists (requiring 1.0 is unattainable at realistic
    # map widths, since it would require the entire bottom row to be floor).
    if has_path(grid) <= 0.0:
        return None

    spawn_exit = _find_spawn_exit(grid)
    if spawn_exit is None:
        return None
    spawn_cell, exit_cell = spawn_exit

    markers = _generate_markers(grid, spawn_cell, exit_cell, seed)

    return CandidateGrid(grid=grid, spawn_cell=spawn_cell, exit_cell=exit_cell, markers=markers)


def _find_spawn_exit(
    grid: np.ndarray,
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Find a spawn cell (near top) and exit cell (near bottom) in the same
    connected floor component. Returns (spawn, exit) as (x, y) tuples, or
    None if no such pair exists.
    """
    passable = grid == 0
    labeled, num_features = ndimage.label(passable)
    if num_features == 0:
        return None

    height, width = grid.shape
    top_labels = set(labeled[0, :].tolist())
    top_labels.discard(0)
    bottom_labels = set(labeled[-1, :].tolist())
    bottom_labels.discard(0)

    connecting_labels = top_labels & bottom_labels
    if not connecting_labels:
        return None

    component_label = sorted(connecting_labels)[0]

    top_cells = np.argwhere(labeled[0, :] == component_label)
    bottom_cells = np.argwhere(labeled[-1, :] == component_label)
    if top_cells.size == 0 or bottom_cells.size == 0:
        return None

    spawn_x = int(top_cells[len(top_cells) // 2, 0])
    exit_x = int(bottom_cells[len(bottom_cells) // 2, 0])

    return (spawn_x, 0), (exit_x, height - 1)


def _generate_markers(
    grid: np.ndarray,
    spawn_cell: tuple[int, int],
    exit_cell: tuple[int, int],
    seed: int,
) -> dict[str, list[tuple[int, int]]]:
    """Deterministically pick a small set of open floor cells for arena and
    loot marker candidates, away from spawn/exit.
    """
    passable_cells = np.argwhere(grid == 0)
    if passable_cells.size == 0:
        return {"arena_candidates": [], "loot_candidates": [], "encounter_zones": []}

    rng = np.random.RandomState(seed)
    excluded = {spawn_cell, exit_cell}
    candidates = [
        (int(x), int(y))
        for y, x in passable_cells
        if (int(x), int(y)) not in excluded
    ]
    rng.shuffle(candidates)

    arena_candidates = candidates[:1]
    loot_candidates = candidates[1:3]

    return {
        "arena_candidates": arena_candidates,
        "loot_candidates": loot_candidates,
        "encounter_zones": [],
    }


def compute_candidate_metrics(
    candidate: CandidateGrid,
    recipe: RecipeConfig,
) -> dict[str, float]:
    """Compute gameplay-facing fitness metrics for a candidate."""
    grid = candidate.grid
    rule = CARule.from_string(recipe.rule_string)

    walkable_ratio = float(np.mean(grid == 0))

    # compute_descriptors returns [coverage(=wall ratio), topology_score, chokepoint_density]
    descriptors = compute_descriptors(grid, rule)
    open_space_score = float(descriptors[1]) if len(descriptors) > 1 else 0.0

    path_length, loop_count, branch_count = _compute_graph_metrics(
        grid, candidate.spawn_cell, candidate.exit_cell
    )

    metrics: dict[str, float] = {
        "walkable_ratio": walkable_ratio,
        "path_length": float(path_length),
        "loop_count": float(loop_count),
        "branch_count": float(branch_count),
        "open_space_score": open_space_score,
    }
    metrics["score"] = _score_from_targets(metrics, recipe.fitness_targets)
    return metrics


def _compute_graph_metrics(
    grid: np.ndarray,
    spawn_cell: tuple[int, int],
    exit_cell: tuple[int, int],
) -> tuple[int, int, int]:
    """Compute (path_length, loop_count, branch_count) over the floor-cell
    adjacency graph (4-connectivity) restricted to the component containing spawn.
    """
    passable = grid == 0
    labeled, _ = ndimage.label(passable)
    spawn_x, spawn_y = spawn_cell
    component_label = labeled[spawn_y, spawn_x]

    component_mask = labeled == component_label
    ys, xs = np.where(component_mask)
    node_count = len(xs)
    if node_count == 0:
        return 0, 0, 0

    # Count edges (4-connectivity, each edge counted once) and node degrees
    right_edges = int(np.sum(component_mask[:, :-1] & component_mask[:, 1:]))
    down_edges = int(np.sum(component_mask[:-1, :] & component_mask[1:, :]))
    edge_count = right_edges + down_edges

    padded = np.pad(component_mask, 1, mode="constant", constant_values=False)
    degree = (
        padded[1:-1, :-2].astype(np.int32)
        + padded[1:-1, 2:].astype(np.int32)
        + padded[:-2, 1:-1].astype(np.int32)
        + padded[2:, 1:-1].astype(np.int32)
    )
    branch_count = int(np.sum((degree >= 3) & component_mask))

    # Cyclomatic number for a connected graph: edges - nodes + 1
    loop_count = max(0, edge_count - node_count + 1)

    path_length = _bfs_path_length(component_mask, spawn_cell, exit_cell)

    return path_length, loop_count, branch_count


def _bfs_path_length(
    component_mask: np.ndarray,
    start: tuple[int, int],
    end: tuple[int, int],
) -> int:
    """Shortest path length (in steps) between start and end within a boolean
    passable mask, using 4-connectivity BFS. Returns 0 if unreachable.
    """
    height, width = component_mask.shape
    start_x, start_y = start
    end_x, end_y = end

    if not component_mask[start_y, start_x] or not component_mask[end_y, end_x]:
        return 0

    visited = np.zeros_like(component_mask, dtype=bool)
    visited[start_y, start_x] = True
    frontier = [(start_x, start_y)]
    steps = 0

    while frontier:
        if (end_x, end_y) in frontier:
            return steps

        next_frontier: list[tuple[int, int]] = []
        for x, y in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and not visited[ny, nx]:
                    if component_mask[ny, nx]:
                        visited[ny, nx] = True
                        next_frontier.append((nx, ny))

        frontier = next_frontier
        steps += 1

    return 0


def _score_from_targets(
    metrics: dict[str, float],
    fitness_targets: dict[str, tuple[float, float]] | None,
) -> float:
    """Deterministic fitness score: fraction of fitness_targets ranges met,
    with partial credit for near-misses.
    """
    if not fitness_targets:
        return 0.75

    per_metric_scores: list[float] = []
    for key, (lo, hi) in fitness_targets.items():
        value = metrics.get(key, 0.0)
        if lo <= value <= hi:
            per_metric_scores.append(1.0)
        else:
            span = max(hi - lo, 1e-6)
            distance = min(abs(value - lo), abs(value - hi))
            per_metric_scores.append(max(0.0, 1.0 - distance / span))

    return sum(per_metric_scores) / len(per_metric_scores)


def tags_from_metrics(metrics: dict[str, float]) -> list[str]:
    """Generate readable tags from metrics."""
    tags = []
    if metrics.get("path_length", 0) > 80:
        tags.append("Long Route")
    elif metrics.get("path_length", 0) < 40:
        tags.append("Short Run")

    if metrics.get("open_space_score", 0) > 0.6:
        tags.append("Open Chambers")
    elif metrics.get("open_space_score", 0) < 0.4:
        tags.append("Tight Tunnels")

    if metrics.get("loop_count", 0) > 3:
        tags.append("Many Loops")

    if metrics.get("branch_count", 0) > 8:
        tags.append("Branching")
    else:
        tags.append("Linear")

    if metrics.get("walkable_ratio", 0) > 0.5:
        tags.append("Arena-Friendly")

    return tags[:4]  # Limit to 4 tags


def encode_grid_rle(grid: np.ndarray) -> str:
    """Encode a 2D grid (0/1 values) as an "rle-v1" run-length string.

    Format: "rle-v1:<count>:<value>:<count>:<value>:..." reading the grid
    row-major (y then x), matching fung_export_service.gd's decoder.
    """
    flat = grid.astype(np.int32).flatten()
    if flat.size == 0:
        return "rle-v1:"

    parts: list[str] = []
    current_value = int(flat[0])
    current_count = 1

    for value in flat[1:]:
        value = int(value)
        if value == current_value:
            current_count += 1
        else:
            parts.append(f"{current_count}:{current_value}")
            current_value = value
            current_count = 1
    parts.append(f"{current_count}:{current_value}")

    return "rle-v1:" + ":".join(parts)


def render_preview_png(grid: np.ndarray, output_path: str) -> bool:
    """Render a small preview PNG of the candidate grid (wall=dark, floor=light).

    Returns True if the image was written, False if Pillow is unavailable.
    """
    try:
        from PIL import Image
    except ImportError:
        return False

    # grid: 1=wall, 0=floor -> map to 0 (black wall) / 255 (white floor)
    pixels = ((1 - grid) * 255).astype(np.uint8)
    image = Image.fromarray(pixels, mode="L")
    image.save(output_path)
    return True


def compute_generation_inputs_hash(
    recipe: RecipeConfig,
    seed: int,
    map_size: tuple[int, int],
    overrides: dict[str, float | str] | None = None,
) -> str:
    """Compute a stable hash of the generation inputs for reproducibility tracking."""
    payload = (
        f"{recipe.id}|{recipe.version}|{recipe.rule_string}|{recipe.initial_density}|"
        f"{recipe.steps}|{seed}|{map_size[0]}x{map_size[1]}|{overrides or {}}"
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
