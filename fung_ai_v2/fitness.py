"""Fitness and descriptor functions for fung_ai_v2.

Extracted from fung_ai_v2.py Section 2 (Papers 14-20).

Bug fixes applied:
  - compute_pattern_entropy: replaced O(n^2) Python loop with vectorized
    sliding_window_view approach (Bug 6).
  - has_path: removed redundant `from scipy import ndimage` inside function
    body; ndimage is imported at module level (Bug 8).

Contains:
  - has_path: top-to-bottom connectivity check
  - _passable_degrees: per-cell Moore-neighbor count
  - compute_pattern_entropy: vectorized Shannon entropy of 3x3 patterns
  - compute_pacing_variance: variance of local open-space density
  - compute_interestingness: combined pattern/pacing score
  - classify_topology: bucket topology_score to label
  - evaluate_ca_rule: full rule evaluation returning fitness + descriptors
  - compute_descriptors: game-design-aware behavior descriptor vector
"""

from typing import Tuple

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy import ndimage

from .ca_engine import CARule, initialize_random, step_ca

_MOORE_KERNEL = np.array([[1, 1, 1],
                          [1, 0, 1],
                          [1, 1, 1]])


def has_path(grid: np.ndarray, top: bool = True, bottom: bool = True) -> float:
    """Check if there's a path from top to bottom using connected-component labeling.

    Returns 1.0 if path exists, 0.0 otherwise.
    For partial connectivity, returns fraction of reachable bottom cells.

    Bug 8 fix: removed redundant `from scipy import ndimage` that was inside
    the original function body; ndimage is imported at module level.
    """
    # Invert: 1 = passable, 0 = wall
    passable = 1 - grid
    labeled, num_features = ndimage.label(passable)

    if num_features == 0:
        return 0.0

    top_components = set(labeled[0, :])
    bottom_components = set(labeled[-1, :])

    connected = top_components & bottom_components
    connected.discard(0)  # Remove background

    if not connected:
        return 0.0

    best_comp = max(connected, key=lambda c: np.sum(labeled[-1, :] == c))
    reachable = np.sum(labeled[-1, :] == best_comp) / grid.shape[1]
    return reachable


def _passable_degrees(grid: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return (passable_mask, per-cell count of passable Moore neighbors)."""
    passable = (1 - grid).astype(np.int32)
    degrees = ndimage.convolve(passable, _MOORE_KERNEL, mode='constant', cval=0)
    return passable.astype(bool), degrees


def compute_pattern_entropy(passable: np.ndarray) -> float:
    """Shannon entropy of local 3x3 passable/wall configurations, normalized to 0-1.

    Bug 6 fix: replaced O(n^2) Python loop (iterating over every cell with
    nested for loops and Counter) with a vectorized implementation using
    sliding_window_view. Each 3x3 window is packed into a 9-bit integer for
    fast unique counting via np.unique.
    """
    if passable.shape[0] < 3 or passable.shape[1] < 3:
        return 0.0

    # Shape: (H-2, W-2, 3, 3)
    windows = sliding_window_view(passable, (3, 3))
    flat = windows.reshape(-1, 9).astype(np.int8)

    # Pack each 9-bit pattern into an integer for fast unique counting.
    powers = (1 << np.arange(9, dtype=np.int16))
    packed = (flat * powers).sum(axis=1)

    _, counts = np.unique(packed, return_counts=True)
    total = len(packed)
    if total == 0:
        return 0.0

    probs = counts / total
    entropy = -np.sum(probs * np.log2(probs + 1e-12))
    max_entropy = 9.0  # log2(2^9) = 9 bits
    return float(min(entropy / max_entropy, 1.0))


def compute_pacing_variance(passable: np.ndarray) -> float:
    """Variance of local open-space density (5x5 windows), proxy for room/corridor pacing."""
    window = ndimage.uniform_filter(passable.astype(np.float64), size=5, mode='constant')
    return float(np.clip(np.var(window) * 4.0, 0.0, 1.0))


def compute_interestingness(grid: np.ndarray) -> float:
    """Combine pattern variety and pacing variance into one 'interesting layout' score."""
    passable = (1 - grid).astype(bool)
    entropy = compute_pattern_entropy(passable)
    pacing = compute_pacing_variance(passable)
    return float(0.5 * entropy + 0.5 * pacing)


def classify_topology(topology_score: float) -> str:
    """Bucket a continuous topology_score into a game-design-facing label."""
    if topology_score < 0.33:
        return "linear"
    elif topology_score < 0.66:
        return "branching"
    else:
        return "open"


def evaluate_ca_rule(
    rule: CARule,
    grid_size: Tuple[int, int],
    seed: int,
    ticks: int = 100,
) -> Tuple[float, np.ndarray]:
    """Evaluate CA rule and return fitness + behavior descriptors.

    Fitness rewards genuinely playable, game-usable caves: traversable,
    structurally interesting, and neither empty nor solid.
    """
    grid = initialize_random(grid_size, seed)
    coverage_history = []

    for t in range(ticks):
        grid = step_ca(grid, rule)
        coverage = float(np.mean(grid))
        coverage_history.append(coverage)

    final_coverage = coverage_history[-1]

    passable_mask, degrees = _passable_degrees(grid)
    total_passable = int(np.sum(passable_mask))

    path_exists = has_path(grid)

    if final_coverage < 0.05:
        # Gate on minimum coverage: extinction (empty/near-empty grid) cannot win.
        fitness = final_coverage * 0.3  # extinction ceiling ~0.015
    else:
        # Reward moderate, cave-like coverage rather than raw coverage (which
        # would bias toward near-solid grids).
        coverage_quality = float(np.clip(1.0 - abs(final_coverage - 0.35) / 0.35, 0.0, 1.0))

        if total_passable == 0:
            chokepoint_density = 0.0
        else:
            chokepoint_density = float(np.sum(degrees[passable_mask] <= 2) / total_passable)
        chokepoint_component = min(chokepoint_density / 0.3, 1.0)

        pacing_component = compute_pacing_variance(passable_mask)
        interestingness = compute_interestingness(grid)

        fitness = (0.30 * coverage_quality +
                   0.30 * path_exists +
                   0.15 * chokepoint_component +
                   0.10 * pacing_component +
                   0.15 * interestingness)

    descriptors = compute_descriptors(grid, rule)

    return fitness, descriptors


def compute_descriptors(grid: np.ndarray, rule: CARule) -> np.ndarray:
    """Compute game-design-aware behavior descriptors for QD archive placement.

    Three-dimensional descriptor space:
    1. Coverage ratio (0-1)
    2. Path topology score (0=linear, ~0.5=branching, 1=open) - derived from the
       average number of passable Moore neighbors per passable cell.
    3. Chokepoint density (0-1) - fraction of passable cells that are narrow
       passages (<=2 passable neighbors).
    """
    coverage = float(np.mean(grid))
    passable_mask, degrees = _passable_degrees(grid)
    total_passable = int(np.sum(passable_mask))

    if total_passable == 0:
        topology_score = 0.0
        chokepoint_density = 0.0
    else:
        passable_degrees = degrees[passable_mask]
        avg_degree = float(np.mean(passable_degrees))
        topology_score = float(np.clip((avg_degree - 2.0) / 6.0, 0.0, 1.0))
        chokepoint_density = float(np.sum(passable_degrees <= 2) / total_passable)

    return np.array([coverage, topology_score, chokepoint_density], dtype=np.float32)
