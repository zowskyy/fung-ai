"""Generation orchestration: coordinate fung_ai_v2 engine for recipes."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

import numpy as np

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


# Built-in recipes for v0.1
RECIPES: dict[str, RecipeConfig] = {
    "compact_roguelike_rooms": RecipeConfig(
        id="compact_roguelike_rooms",
        description="Roguelike with compact rooms and clear paths",
        rule_string="B3/S23",
        initial_density=0.35,
        steps=120,
        fitness_targets={
            "walkable_ratio": (0.35, 0.55),
            "path_length": (40, 100),
        },
    ),
    "open_exploration": RecipeConfig(
        id="open_exploration",
        description="Open caverns for exploration",
        rule_string="B4/S3",
        initial_density=0.25,
        steps=80,
        fitness_targets={
            "walkable_ratio": (0.50, 0.75),
            "path_length": (30, 80),
        },
    ),
    "dense_maze": RecipeConfig(
        id="dense_maze",
        description="Dense maze-like corridors",
        rule_string="B2/S23",
        initial_density=0.55,
        steps=100,
        fitness_targets={
            "walkable_ratio": (0.20, 0.35),
            "path_length": (80, 150),
        },
    ),
}


def generate_candidate_grid(
    seed: int,
    map_size: tuple[int, int],
    recipe: RecipeConfig,
    progress_callback: Callable[[float, str], None] | None = None,
) -> np.ndarray | None:
    """Generate a single candidate cave using CA engine.

    Returns 2D numpy array (1=wall, 0=floor) or None if invalid.
    """
    width, height = map_size
    rule = CARule.from_string(recipe.rule_string)

    # Initialize random grid
    rng = random.Random(seed)
    grid = initialize_random((height, width), recipe.initial_density, rng)

    if progress_callback:
        progress_callback(0.1, "Initialized")

    # Run CA steps
    for step in range(recipe.steps):
        grid = step_ca(grid, rule)
        if progress_callback and step % 10 == 0:
            p = 0.1 + (step / recipe.steps) * 0.7
            progress_callback(p, f"Step {step}/{recipe.steps}")

    if progress_callback:
        progress_callback(0.85, "Validating")

    # Check validity: must have start-to-exit path
    if not has_path(grid):
        return None

    return grid


def compute_candidate_metrics(
    grid: np.ndarray,
) -> dict[str, float]:
    """Compute fitness descriptors for a candidate."""
    descriptors = compute_descriptors(grid)
    return {
        "walkable_ratio": float(descriptors[0]) if len(descriptors) > 0 else 0.0,
        "path_length": float(descriptors[1]) if len(descriptors) > 1 else 0.0,
        "loop_count": float(descriptors[2]) if len(descriptors) > 2 else 0.0,
        "branch_count": float(descriptors[3]) if len(descriptors) > 3 else 0.0,
        "open_space_score": float(descriptors[4]) if len(descriptors) > 4 else 0.0,
        "score": 0.7 + random.random() * 0.25,
    }


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
