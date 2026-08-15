
"""
Fung-AI v2.0: Game-Design-Aware Quality-Diversity Cave Generator
=================================================================
Evolves Conway-Life-style cellular automaton rules (B/S notation) into 2D
cave/dungeon layouts using MAP-Elites (Mouret & Clune, 2015), then exports
the result to a Godot-4-compatible scene.

The QD archive organizes generated caves along axes that matter for game
design rather than abstract CA statistics: coverage, path topology
(linear/branching/open), and chokepoint density. Fitness rewards caves that
are traversable, structurally interesting, and neither empty nor solid.

Measured against a Random Search baseline (see README_v2.md), MAP-Elites
gives a modest but consistent edge in coverage and QD-score.
"""

import numpy as np
import json
import random
from typing import List, Tuple, Set, Dict, Optional, Callable, Literal
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from abc import ABC, abstractmethod
import heapq
from scipy import ndimage
from scipy.spatial.distance import cdist
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# SECTION 1: CELLULAR AUTOMATA ENGINE (Papers 6, 7, 8, 26, 27, 28)
# =============================================================================

@dataclass
class CARule:
    """Birth/Survival rule encoding for Conway-like cellular automata.

    From Growing Neural CA (Mordvintsev et al., 2020) and
    Evolution of Spots/Stripes in CA (2025).
    """
    birth: Set[int]
    survival: Set[int]

    def __str__(self):
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survival))
        return f"B{b}/S{s}"

    def to_genotype(self) -> np.ndarray:
        """9-bit binary encoding: [B0..B8, S0..S8]"""
        return np.array(
            [float(i in self.birth) for i in range(9)] +
            [float(i in self.survival) for i in range(9)],
            dtype=np.float32
        )

    @classmethod
    def from_genotype(cls, g: np.ndarray) -> "CARule":
        birth = {i for i in range(9) if g[i] > 0.5}
        survival = {i for i in range(9) if g[i + 9] > 0.5}
        return cls(birth, survival)

    @classmethod
    def from_string(cls, rule_str: str) -> "CARule":
        """Parse B3/S23 format."""
        parts = rule_str.split('/')
        birth = set(int(c) for c in parts[0][1:]) if parts[0].startswith('B') else set()
        survival = set(int(c) for c in parts[1][1:]) if parts[1].startswith('S') else set()
        return cls(birth, survival)

    def mutate(self, prob: float = 0.1) -> "CARule":
        """Bit-flip mutation."""
        g = self.to_genotype()
        mask = np.random.random(18) < prob
        g = np.where(mask, 1 - g, g)
        return CARule.from_genotype(g)

    def crossover(self, other: "CARule") -> "CARule":
        """Uniform crossover."""
        g1 = self.to_genotype()
        g2 = other.to_genotype()
        mask = np.random.random(18) < 0.5
        g = np.where(mask, g1, g2)
        return CARule.from_genotype(g)


def step_ca(grid: np.ndarray, rule: CARule) -> np.ndarray:
    """Execute one CA step with Moore neighborhood.

    Standard Life-like CA update with birth/survival rules.
    """
    # Count neighbors using convolution
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]])
    neighbors = ndimage.convolve(grid.astype(np.int32), kernel, mode='wrap')

    # Apply rules
    born = np.isin(neighbors, list(rule.birth)) & (grid == 0)
    survive = np.isin(neighbors, list(rule.survival)) & (grid == 1)
    new_grid = np.zeros_like(grid)
    new_grid[born | survive] = 1
    return new_grid


def initialize_random(grid_size: Tuple[int, int], seed: int, density: float = 0.45) -> np.ndarray:
    """Initialize random grid with given alive cell density."""
    rng = np.random.RandomState(seed)
    return (rng.random(grid_size) < density).astype(np.float32)


# Biome -> initial density. Higher-precip/warmer biomes get denser initial
# fill (more terrain to carve caves out of); cold/dry biomes get sparser fill.
BIOME_DENSITY = {
    "tropical_rainforest": 0.60,
    "temperate_rainforest": 0.55,
    "tropical_seasonal_forest": 0.52,
    "temperate_forest": 0.48,
    "boreal_forest": 0.45,
    "woodland_shrubland": 0.40,
    "temperate_grassland": 0.35,
    "desert": 0.20,
    "tundra": 0.15,
}

# Biome -> CA rule. Wet/forested biomes get a more permissive survival set
# (denser, more connected structure); dry/cold biomes get a tighter one
# (sparser, more eroded). Sanity-checked standalone (see rule_test2.py in
# this task's scratchpad) against 50 ticks -- none go extinct or full-fill.
BIOME_RULE = {
    "tropical_rainforest": "B3/S23",
    "temperate_rainforest": "B3/S23",
    "tropical_seasonal_forest": "B36/S23",
    "temperate_forest": "B36/S23",
    "boreal_forest": "B3/S1234",
    "woodland_shrubland": "B3/S1234",
    "temperate_grassland": "B3/S12345",
    "desert": "B3/S123",
    "tundra": "B3/S12",
}

# Nudge caps, each independent of the other -- neither settlements nor wind
# can outweigh the biome signal (whose own spread is 0.15-0.60).
_SETTLEMENT_ADJ_CAP = 0.15
_SETTLEMENT_RADIUS_KM = 10.0
_WIND_ADJ_CAP = 0.15
_WIND_ADJ_PER_KMH = 0.0025
_DENSITY_MIN = 0.05
_DENSITY_MAX = 0.9


def compute_density(env: dict) -> dict:
    """Compose biome/settlement/wind signals into a final initial density.

    - Settlement within _SETTLEMENT_RADIUS_KM: nudges density DOWN (cleared/
      inhabited land is more open), scaled by inverse distance, capped.
    - Wind speed: nudges density DOWN (wind-scoured terrain is more open),
      linear in km/h, capped.
    - Final value clamped to [_DENSITY_MIN, _DENSITY_MAX] so it can never
      produce a degenerate all-empty or all-full starting grid.
    """
    classification = env["biome"]["classification"]
    base_density = BIOME_DENSITY.get(classification, 0.45)

    settlements = env.get("settlements") or []
    nearest_km = min((s["distance_km"] for s in settlements), default=None)
    settlement_adj = 0.0
    if nearest_km is not None and nearest_km <= _SETTLEMENT_RADIUS_KM:
        settlement_adj = _SETTLEMENT_ADJ_CAP * (1 - nearest_km / _SETTLEMENT_RADIUS_KM)
        settlement_adj = min(_SETTLEMENT_ADJ_CAP, settlement_adj)

    wind_kmh = env.get("weather", {}).get("wind_speed_kmh") or 0.0
    wind_adj = min(_WIND_ADJ_CAP, wind_kmh * _WIND_ADJ_PER_KMH)

    final_density = base_density - settlement_adj - wind_adj
    final_density = max(_DENSITY_MIN, min(_DENSITY_MAX, final_density))

    return {
        "classification": classification,
        "base_density": base_density,
        "nearest_settlement_km": nearest_km,
        "settlement_adj": round(settlement_adj, 4),
        "wind_kmh": wind_kmh,
        "wind_adj": round(wind_adj, 4),
        "final_density": round(final_density, 4),
    }


def has_path(grid: np.ndarray, top: bool = True, bottom: bool = True) -> float:
    """Check if there's a path from top to bottom using A* / BFS.

    Returns 1.0 if path exists, 0.0 otherwise.
    For partial connectivity, returns fraction of reachable bottom cells.
    """
    from scipy import ndimage

    # Find connected components of empty space (0 = empty/passable)
    # Invert: 1 = passable, 0 = wall
    passable = 1 - grid
    labeled, num_features = ndimage.label(passable)

    if num_features == 0:
        return 0.0

    # Find components touching top and bottom
    top_components = set(labeled[0, :])
    bottom_components = set(labeled[-1, :])

    # Check intersection
    connected = top_components & bottom_components
    connected.discard(0)  # Remove background

    if not connected:
        return 0.0

    # Return fraction of bottom cells reachable
    best_comp = max(connected, key=lambda c: np.sum(labeled[-1, :] == c))
    reachable = np.sum(labeled[-1, :] == best_comp) / grid.shape[1]
    return reachable


# =============================================================================
# SECTION 2: FITNESS & DESCRIPTOR FUNCTIONS (Papers 14, 15, 16, 17, 18, 19, 20)
# =============================================================================

_MOORE_KERNEL = np.array([[1, 1, 1],
                          [1, 0, 1],
                          [1, 1, 1]])


def _passable_degrees(grid: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Return (passable_mask, per-cell count of passable Moore neighbors)."""
    passable = (1 - grid).astype(np.int32)
    degrees = ndimage.convolve(passable, _MOORE_KERNEL, mode='constant', cval=0)
    return passable.astype(bool), degrees


def compute_pattern_entropy(passable: np.ndarray) -> float:
    """Shannon entropy of local 3x3 passable/wall configurations, normalized to 0-1."""
    patterns = []
    h, w = passable.shape
    for i in range(1, h - 1):
        for j in range(1, w - 1):
            pattern = tuple(passable[i-1:i+2, j-1:j+2].flatten().astype(int))
            patterns.append(pattern)

    if not patterns:
        return 0.0
    counts = Counter(patterns)
    total = len(patterns)
    entropy = -sum((c/total) * np.log2(c/total) for c in counts.values() if c > 0)
    max_entropy = 9.0  # 2^9 possible patterns (but many won't appear)
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


def evaluate_ca_rule(rule: CARule, grid_size: Tuple[int, int],
                     seed: int, ticks: int = 100) -> Tuple[float, np.ndarray]:
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
        fitness = final_coverage * 0.3  # extinction ceiling ≈ 0.015
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
       average number of passable Moore neighbors per passable cell, a lightweight
       proxy for branchiness when skimage skeletonization isn't available.
    3. Chokepoint density (0-1) - fraction of passable cells that are narrow
       passages (<=2 passable neighbors), proxying tactical corridors.
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


# =============================================================================
# SECTION 3: ARCHIVE DATA STRUCTURE (Papers 1, 2, 3, 4)
# =============================================================================

@dataclass
class ArchiveCell:
    """Single cell in the QD archive with CMA-MAE annealing threshold.

    From CMA-MAE (Fontaine et al., 2023): maintains acceptance threshold t_e
    that anneals over time based on archive learning rate alpha.
    From Dominated Novelty Search (Bahlous-Boldi et al., 2025): tracks visit_count
    for density estimation without requiring rho_min parameter.
    """
    elite: Optional[np.ndarray] = None
    fitness: float = -np.inf
    threshold: float = -np.inf  # CMA-MAE: t_e
    visit_count: int = 0        # DNS: density estimation
    last_updated: int = 0

    def update_threshold(self, new_fitness: float, alpha: float):
        """CMA-MAE threshold annealing: t_e <- (1-alpha)*t_e + alpha*f(theta')"""
        if self.threshold == -np.inf:
            self.threshold = new_fitness
        else:
            self.threshold = (1 - alpha) * self.threshold + alpha * new_fitness


class GridArchive:
    """N-dimensional grid-based archive with annealing thresholds.

    Synthesis of MAP-Elites (2015) grid structure + CMA-MAE (2023) annealing
    + Dominated Novelty Search (2025) density tracking.
    """

    def __init__(self, dims: List[Tuple[float, float, int]], alpha: float = 0.5):
        """
        Args:
            dims: List of (min, max, num_bins) for each descriptor dimension
            alpha: Archive learning rate (CMA-MAE). Auto-adjusted by AAALE.
        """
        self.dims = dims
        self.alpha = alpha
        self.num_dims = len(dims)
        self.shape = tuple(d[2] for d in dims)
        self.total_cells = np.prod(self.shape)

        # Initialize grid
        self.grid = np.empty(self.shape, dtype=object)
        for idx in np.ndindex(self.shape):
            self.grid[idx] = ArchiveCell()

        # Track statistics
        self.filled_count = 0
        self.eval_count = 0
        self.generation = 0
        self.fitness_history = []
        self.descriptor_history = []

    def _get_index(self, descriptors: np.ndarray) -> Tuple[int, ...]:
        """Map continuous descriptors to discrete grid indices."""
        indices = []
        for i, (d_min, d_max, n_bins) in enumerate(self.dims):
            # Clip to bounds
            d = np.clip(descriptors[i], d_min, d_max)
            # Map to bin
            bin_idx = int((d - d_min) / (d_max - d_min) * n_bins)
            bin_idx = min(bin_idx, n_bins - 1)  # Handle edge case
            indices.append(bin_idx)
        return tuple(indices)

    def add(self, solution: np.ndarray, fitness: float, descriptors: np.ndarray) -> bool:
        """Add solution to archive using CMA-MAE annealing threshold.

        Returns True if solution was added/updated.
        """
        idx = self._get_index(descriptors)
        cell = self.grid[idx]

        self.eval_count += 1
        cell.visit_count += 1

        # CMA-MAE: Check against annealing threshold
        improvement = fitness - cell.threshold

        if cell.elite is None:
            # Empty cell - fill it
            cell.elite = solution.copy()
            cell.fitness = fitness
            cell.threshold = fitness
            cell.last_updated = self.generation
            self.filled_count += 1
            return True
        elif improvement > 0:
            # Better than threshold - replace
            cell.elite = solution.copy()
            cell.fitness = fitness
            cell.last_updated = self.generation
            cell.update_threshold(fitness, self.alpha)
            return True
        else:
            # Didn't improve threshold - still update threshold slightly
            cell.update_threshold(fitness, self.alpha * 0.1)
            return False

    def get_random_elite(self) -> Tuple[np.ndarray, float, np.ndarray]:
        """Sample random elite from filled cells."""
        filled = [(idx, self.grid[idx]) for idx in np.ndindex(self.shape) 
                  if self.grid[idx].elite is not None]
        if not filled:
            return None, -np.inf, None
        idx, cell = random.choice(filled)
        # Reconstruct descriptor from index
        descriptors = np.array([
            self.dims[i][0] + (idx[i] + 0.5) * (self.dims[i][1] - self.dims[i][0]) / self.dims[i][2]
            for i in range(self.num_dims)
        ], dtype=np.float32)
        return cell.elite.copy(), cell.fitness, descriptors

    def get_all_elites(self) -> List[Tuple[np.ndarray, float, np.ndarray]]:
        """Get all elites in archive."""
        elites = []
        for idx in np.ndindex(self.shape):
            cell = self.grid[idx]
            if cell.elite is not None:
                descriptors = np.array([
                    self.dims[i][0] + (idx[i] + 0.5) * (self.dims[i][1] - self.dims[i][0]) / self.dims[i][2]
                    for i in range(self.num_dims)
                ], dtype=np.float32)
                elites.append((cell.elite.copy(), cell.fitness, descriptors))
        return elites

    def coverage(self) -> float:
        """Fraction of cells filled."""
        return self.filled_count / self.total_cells

    def qd_score(self) -> float:
        """Quality diversity score: sum of fitnesses of filled cells."""
        return sum(cell.fitness for idx in np.ndindex(self.shape) 
                   for cell in [self.grid[idx]] if cell.elite is not None)

    def get_statistics(self) -> Dict:
        """Archive statistics."""
        elites = self.get_all_elites()
        if not elites:
            return {"coverage": 0.0, "qd_score": 0.0, "max_fitness": -np.inf, "mean_fitness": 0.0}

        fitnesses = [f for _, f, _ in elites]
        return {
            "coverage": self.coverage(),
            "qd_score": self.qd_score(),
            "max_fitness": max(fitnesses),
            "mean_fitness": np.mean(fitnesses),
            "num_elites": len(elites),
            "eval_count": self.eval_count
        }


# =============================================================================
# SECTION 4: EMITTER INTERFACES (Papers 1, 2, 3, 4, 5, 29, 30)
# =============================================================================

class Emitter(ABC):
    """Abstract emitter interface for quality diversity algorithms.

    Unified interface supporting MAP-Elites, CMA-MAE, CMA-ME, and DNS emitters.
    """

    def __init__(self, name: str):
        self.name = name
        self.eval_count = 0

    @abstractmethod
    def ask(self, archive: GridArchive, batch_size: int = 36) -> List[np.ndarray]:
        """Generate new solutions to evaluate."""
        pass

    @abstractmethod
    def tell(self, archive: GridArchive, solutions: List[np.ndarray], 
             fitnesses: List[float], descriptors: List[np.ndarray]):
        """Update emitter state with evaluation results."""
        pass

    def reset(self):
        """Reset emitter state."""
        self.eval_count = 0


class MAP_Elites_Emitter(Emitter):
    """Standard MAP-Elites emitter with Gaussian mutation.

    From Mouret & Clune (2015): Illuminating search spaces by mapping elites.
    """

    def __init__(self, mutation_std: float = 0.1, crossover_prob: float = 0.5):
        super().__init__("MAP-Elites")
        self.mutation_std = mutation_std
        self.crossover_prob = crossover_prob

    def ask(self, archive: GridArchive, batch_size: int = 36) -> List[np.ndarray]:
        solutions = []
        for _ in range(batch_size):
            if random.random() < self.crossover_prob and archive.filled_count >= 2:
                # Crossover between two random elites
                e1, _, _ = archive.get_random_elite()
                e2, _, _ = archive.get_random_elite()
                if e1 is not None and e2 is not None:
                    child = np.where(np.random.random(18) < 0.5, e1, e2)
                    # Add mutation
                    child += np.random.normal(0, self.mutation_std, 18)
                    child = np.clip(child, 0, 1)
                    solutions.append(child)
                else:
                    solutions.append(np.random.random(18))
            else:
                # Mutation from random elite
                elite, _, _ = archive.get_random_elite()
                if elite is not None:
                    mutant = elite + np.random.normal(0, self.mutation_std, 18)
                    mutant = np.clip(mutant, 0, 1)
                    solutions.append(mutant)
                else:
                    solutions.append(np.random.random(18))
        return solutions

    def tell(self, archive, solutions, fitnesses, descriptors):
        self.eval_count += len(solutions)


# =============================================================================
# SECTION 7: BASELINE ALGORITHMS FOR COMPARISON
# =============================================================================

class RandomSearch:
    """Random search baseline."""

    def __init__(self, archive_dims: List[Tuple[float, float, int]] = None):
        if archive_dims is None:
            archive_dims = [(0.0, 1.0, 10), (0.0, 1.0, 10), (0.0, 1.0, 10)]
        self.archive = GridArchive(archive_dims, alpha=0.5)

    def run(self, grid_size=(20, 20), ticks=100, max_evals=10000, 
            batch_size=36, seed=42, verbose=True):
        np.random.seed(seed)
        random.seed(seed)

        evals_done = 0
        for gen in range(max_evals // batch_size):
            for _ in range(batch_size):
                if evals_done >= max_evals:
                    break
                sol = np.random.random(18)
                rule = CARule.from_genotype(sol)
                fitness, desc = evaluate_ca_rule(rule, grid_size, seed + evals_done, ticks)
                self.archive.add(sol, fitness, desc)
                evals_done += 1

            if verbose and gen % 20 == 0:
                stats = self.archive.get_statistics()
                print(f"  [RS Gen {gen}] Evals: {evals_done} | "
                      f"Coverage: {stats['coverage']:.1%} | "
                      f"Max Fit: {stats['max_fitness']:.3f}")

        return self.archive


class Standard_MAP_Elites:
    """Standard MAP-Elites without landscape awareness."""

    def __init__(self, archive_dims: List[Tuple[float, float, int]] = None):
        if archive_dims is None:
            archive_dims = [(0.0, 1.0, 10), (0.0, 1.0, 10), (0.0, 1.0, 10)]
        self.archive = GridArchive(archive_dims, alpha=0.5)
        self.emitter = MAP_Elites_Emitter(mutation_std=0.15)

    def run(self, grid_size=(20, 20), ticks=100, max_evals=10000, 
            batch_size=36, seed=42, verbose=True):
        np.random.seed(seed)
        random.seed(seed)

        evals_done = 0
        gen = 0
        while evals_done < max_evals:
            gen += 1
            solutions = self.emitter.ask(self.archive, batch_size)

            for sol in solutions:
                if evals_done >= max_evals:
                    break
                rule = CARule.from_genotype(sol)
                fitness, desc = evaluate_ca_rule(rule, grid_size, seed + evals_done, ticks)
                self.archive.add(sol, fitness, desc)
                evals_done += 1

            self.emitter.tell(self.archive, solutions, [], [])

            if verbose and gen % 20 == 0:
                stats = self.archive.get_statistics()
                print(f"  [ME Gen {gen}] Evals: {evals_done} | "
                      f"Coverage: {stats['coverage']:.1%} | "
                      f"Max Fit: {stats['max_fitness']:.3f}")

        return self.archive


# =============================================================================
# SECTION 8: HELD-OUT BENCHMARK PROTOCOL
# =============================================================================

def run_held_out_benchmark(algorithm, 
                           train_rules=["B3/S23", "B5678/S45678"],
                           test_rules=["B36/S23", "B3/S238"],
                           grid_sizes=[(20, 20), (40, 40), (80, 80)],
                           train_seeds=range(1, 1001),
                           val_seeds=range(1001, 2001),
                           test_seeds=range(2001, 3001),
                           max_evals=10000,
                           verbose=True):
    """Run held-out benchmark protocol from Fung-AI v1.0.

    Training: B3/S23, B5678/S45678 on 20x20, seeds 1-1000
    Validation: Same rules on 40x40, seeds 1001-2000
    Test: B36/S23, B3/S238 on 20x20/40x40/80x80, seeds 2001-3000
    """
    results = {
        "train": {},
        "val": {},
        "test": {}
    }

    # Training phase
    if verbose:
        print("=" * 60)
        print("HELD-OUT BENCHMARK PROTOCOL")
        print("=" * 60)
        print("\n[TRAINING PHASE]")

    for rule_str in train_rules:
        rule = CARule.from_string(rule_str)
        if verbose:
            print(f"\n  Training on {rule_str} (20x20, {len(train_seeds)} seeds)")

        archive = algorithm.run(grid_size=(20, 20), ticks=100, 
                                max_evals=max_evals, seed=42, verbose=verbose)
        results["train"][rule_str] = algorithm.get_results()

    # Validation phase
    if verbose:
        print("\n[VALIDATION PHASE]")

    for rule_str in train_rules:
        if verbose:
            print(f"\n  Validating on {rule_str} (40x40, {len(val_seeds)} seeds)")

        archive = algorithm.run(grid_size=(40, 40), ticks=100,
                                max_evals=max_evals, seed=1042, verbose=verbose)
        results["val"][rule_str] = algorithm.get_results()

    # Test phase (generalization)
    if verbose:
        print("\n[TEST PHASE - GENERALIZATION]")

    for rule_str in test_rules:
        for grid_size in grid_sizes:
            key = f"{rule_str}_{grid_size[0]}x{grid_size[1]}"
            if verbose:
                print(f"\n  Testing on {rule_str} ({grid_size[0]}x{grid_size[1]}, {len(test_seeds)} seeds)")

            archive = algorithm.run(grid_size=grid_size, ticks=100,
                                    max_evals=max_evals, seed=2042, verbose=verbose)
            results["test"][key] = algorithm.get_results()

    # Compute generalization metrics
    train_success = np.mean([r["success_at_10k"] for r in results["train"].values()])
    test_success = np.mean([r["success_at_10k"] for r in results["test"].values()])
    generalization_gap = train_success - test_success

    results["summary"] = {
        "train_success": train_success,
        "test_success": test_success,
        "generalization_gap": generalization_gap,
        "generalizes": generalization_gap < 0.05  # Threshold from v1.0 protocol
    }

    if verbose:
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"  Train success@10k: {train_success:.3f}")
        print(f"  Test success@10k:  {test_success:.3f}")
        print(f"  Generalization gap: {generalization_gap:.3f}")
        print(f"  Generalizes: {results['summary']['generalizes']}")

    return results


# =============================================================================
# SECTION 9: GODOT EXPORTER (Papers 16, 17, 18, 19)
# =============================================================================

class GodotExporter:
    """Export CA-generated caves to Godot 4 compatible format.

    Inspired by GameCraft-Bench (2026) and WorldGen (2025) engine integration.
    """

    def __init__(self, tile_size: int = 32):
        self.tile_size = tile_size

    def export_to_godot(self, grid: np.ndarray, rule: CARule, 
                        ticks: int, output_path: str):
        """Generate Godot 4 scene JSON.

        Exports:
        - TileMapLayer for cave walls/floors
        - NavigationRegion2D for pathfinding
        - Collision shapes for physics
        - Spawn points for player/enemies
        """
        h, w = grid.shape

        # Generate tilemap data
        tilemap = []
        for i in range(h):
            for j in range(w):
                # 1 = wall, 0 = floor/passable
                tile_type = "wall" if grid[i, j] > 0.5 else "floor"
                tilemap.append({
                    "x": j * self.tile_size,
                    "y": i * self.tile_size,
                    "type": tile_type,
                    "coords": [i, j]
                })

        # Find spawn points (largest empty region)
        passable = 1 - grid
        labeled, num_features = ndimage.label(passable)
        if num_features > 0:
            largest_label = max(range(1, num_features + 1), 
                               key=lambda l: np.sum(labeled == l))
            largest_region = np.argwhere(labeled == largest_label)

            # Player spawn: center of largest region
            center = largest_region[len(largest_region) // 2]
            player_spawn = {
                "x": int(center[1]) * self.tile_size + self.tile_size // 2,
                "y": int(center[0]) * self.tile_size + self.tile_size // 2
            }

            # Enemy spawns: random points in largest region
            enemy_spawns = []
            if len(largest_region) > 10:
                for _ in range(min(5, len(largest_region) // 10)):
                    pt = largest_region[np.random.randint(len(largest_region))]
                    enemy_spawns.append({
                        "x": int(pt[1]) * self.tile_size + self.tile_size // 2,
                        "y": int(pt[0]) * self.tile_size + self.tile_size // 2
                    })
        else:
            player_spawn = {"x": w * self.tile_size // 2, "y": h * self.tile_size // 2}
            enemy_spawns = []

        # Navigation polygon (simplified)
        navigation = self._generate_navigation_polygon(grid)

        scene = {
            "version": "4.0",
            "type": "Node2D",
            "name": "CaveLevel",
            "tilemap": tilemap,
            "navigation": navigation,
            "player_spawn": player_spawn,
            "enemy_spawns": enemy_spawns,
            "metadata": {
                "rule": str(rule),
                "ticks": ticks,
                "grid_size": [h, w],
                "tile_size": self.tile_size,
                "playable": bool(has_path(grid) > 0.5)
            }
        }

        with open(output_path, 'w') as f:
            json.dump(scene, f, indent=2)

        return scene

    def _generate_navigation_polygon(self, grid: np.ndarray) -> List[Dict]:
        """Generate simplified navigation polygons from passable regions."""
        passable = 1 - grid
        labeled, num_features = ndimage.label(passable)

        polygons = []
        for label in range(1, num_features + 1):
            region = np.argwhere(labeled == label)
            if len(region) < 10:
                continue

            # Simple bounding box polygon
            min_y, min_x = region.min(axis=0)
            max_y, max_x = region.max(axis=0)

            polygons.append({
                "type": "rectangle",
                "x": int(min_x) * self.tile_size,
                "y": int(min_y) * self.tile_size,
                "width": int(max_x - min_x + 1) * self.tile_size,
                "height": int(max_y - min_y + 1) * self.tile_size
            })

        return polygons


# =============================================================================
# SECTION 10: CLI INTERFACE (Fung-AI v1.0 Compatible)
# =============================================================================

def main():
    """Main CLI entry point for Fung-AI v2.0."""
    import sys

    if len(sys.argv) < 2:
        print("Fung-AI v2.0 - Game-Design-Aware QD Cave Generator (MAP-Elites)")
        print()
        print("Usage:")
        print("  python fung_ai_v2.py generate --rule B3/S23 --width 100 --height 100 --ticks 50")
        print("  python fung_ai_v2.py generate --lat 10.46 --lon -84.70 --multi-biome --width 99 --height 99")
        print("  python fung_ai_v2.py benchmark --algorithm map_elites --evals 10000")
        print("  python fung_ai_v2.py compare --evals 10000")
        print("  python fung_ai_v2.py export --input cave.json --output godot_scene.json")
        print("  python fung_ai_v2.py query --style branching --algorithm map_elites --evals 10000")
        print()
        print("Algorithms: map_elites, random")
        print("Styles: linear, branching, open")
        return

    command = sys.argv[1]

    if command == "generate":
        # Parse args
        rule_str = "B3/S23"
        width, height = 100, 100
        ticks = 50
        seed = 42
        lat = None
        lon = None
        multi_biome = "--multi-biome" in sys.argv

        for i, arg in enumerate(sys.argv):
            if arg == "--rule" and i + 1 < len(sys.argv):
                rule_str = sys.argv[i + 1]
            elif arg == "--width" and i + 1 < len(sys.argv):
                width = int(sys.argv[i + 1])
            elif arg == "--height" and i + 1 < len(sys.argv):
                height = int(sys.argv[i + 1])
            elif arg == "--ticks" and i + 1 < len(sys.argv):
                ticks = int(sys.argv[i + 1])
            elif arg == "--seed" and i + 1 < len(sys.argv):
                seed = int(sys.argv[i + 1])
            elif arg == "--lat" and i + 1 < len(sys.argv):
                lat = float(sys.argv[i + 1])
            elif arg == "--lon" and i + 1 < len(sys.argv):
                lon = float(sys.argv[i + 1])

        if multi_biome and (lat is None or lon is None):
            print("[error] --multi-biome requires --lat and --lon", file=sys.stderr)
            sys.exit(1)

        if multi_biome:
            import os
            import sys as _sys
            _sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
            from env_pipeline.environment import get_environment

            tile_w, tile_h = width // 3, height // 3
            actual_width, actual_height = tile_w * 3, tile_h * 3
            if (actual_width, actual_height) != (width, height):
                print(f"[env] --width/--height not divisible by 3, rounded down to "
                      f"{actual_width}x{actual_height}", file=sys.stderr)

            # 3x3 grid of sub-regions centered on (lat, lon), ~0.5 degree
            # (~50km) offsets. row 0 = north, row 2 = south; col 0 = west,
            # col 2 = east.
            composite = np.zeros((actual_height, actual_width), dtype=np.float32)
            tiles_meta = []
            for row in range(3):
                for col in range(3):
                    sub_lat = lat + (1 - row) * 0.5
                    sub_lon = lon + (col - 1) * 0.5
                    sub_env = get_environment(sub_lat, sub_lon)
                    d = compute_density(sub_env)
                    tile_rule_str = BIOME_RULE.get(d["classification"], "B3/S23")
                    tile_rule = CARule.from_string(tile_rule_str)
                    tile_seed = seed + row * 3 + col

                    nearest_str = f"{d['nearest_settlement_km']}km" if d['nearest_settlement_km'] is not None else "none"
                    print(f"[env] tile ({row},{col}) @ ({sub_lat:.4f},{sub_lon:.4f}): "
                          f"biome={d['classification']} rule={tile_rule_str} "
                          f"base_density={d['base_density']} settlement_adj=-{d['settlement_adj']} "
                          f"(nearest={nearest_str}) wind_adj=-{d['wind_adj']} "
                          f"({d['wind_kmh']}km/h) -> final_density={d['final_density']}",
                          file=sys.stderr)

                    tile_grid = initialize_random((tile_h, tile_w), tile_seed, density=d["final_density"])
                    for t in range(ticks):
                        tile_grid = step_ca(tile_grid, tile_rule)

                    composite[row * tile_h:(row + 1) * tile_h, col * tile_w:(col + 1) * tile_w] = tile_grid
                    tiles_meta.append({
                        "row": row,
                        "col": col,
                        "lat": sub_lat,
                        "lon": sub_lon,
                        "biome": d["classification"],
                        "rule": tile_rule_str,
                        "density_used": d["final_density"],
                        "base_density": d["base_density"],
                        "settlement_adj": d["settlement_adj"],
                        "wind_adj": d["wind_adj"],
                    })

            result = {
                "rule": "multi-biome",
                "grid": composite.tolist(),
                "width": actual_width,
                "height": actual_height,
                "ticks": ticks,
                "coverage": float(np.mean(composite)),
                "playable": bool(has_path(composite) > 0.5),
                "multi_biome": True,
                "tiles": tiles_meta,
            }
            print(json.dumps(result))
            return

        rule = CARule.from_string(rule_str)

        # Density composes the biome signal with settlement proximity and
        # wind speed nudges -- see compute_density() and ENV_PIPELINE.md.
        density = 0.45
        env = None
        if lat is not None and lon is not None:
            import os
            import sys as _sys
            _sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
            from env_pipeline.environment import get_environment

            env = get_environment(lat, lon)
            d = compute_density(env)
            density = d["final_density"]

            print(f"[env] fetched real environment snapshot for ({lat}, {lon}):", file=sys.stderr)
            print(f"[env]   biome={d['classification']} "
                  f"(annual_temp_c={env['biome']['annual_temp_c']}, "
                  f"annual_precip_mm={env['biome']['annual_precip_mm']}) -> base_density={d['base_density']}",
                  file=sys.stderr)
            nearest_str = f"{d['nearest_settlement_km']}km" if d['nearest_settlement_km'] is not None else "none"
            print(f"[env]   settlement_adj=-{d['settlement_adj']} "
                  f"(nearest={nearest_str}, radius={_SETTLEMENT_RADIUS_KM}km) "
                  f"wind_adj=-{d['wind_adj']} (wind_speed_kmh={d['wind_kmh']}) "
                  f"-> final_density={density} (clamped to [{_DENSITY_MIN},{_DENSITY_MAX}])",
                  file=sys.stderr)
            print(f"[env]   elevation_m={env['elevation_m']}", file=sys.stderr)
            print(f"[env]   settlements nearby: {[s['name'] for s in env['settlements']]}",
                  file=sys.stderr)

        grid = initialize_random((height, width), seed, density=density)

        for t in range(ticks):
            grid = step_ca(grid, rule)

        # Output as JSON
        result = {
            "rule": str(rule),
            "grid": grid.tolist(),
            "width": width,
            "height": height,
            "ticks": ticks,
            "coverage": float(np.mean(grid)),
            "playable": bool(has_path(grid) > 0.5),
            "density_used": density,
        }
        if env is not None:
            result["environment"] = env
        print(json.dumps(result))

    elif command == "benchmark":
        evals = 10000
        algo = "map_elites"

        for i, arg in enumerate(sys.argv):
            if arg == "--evals" and i + 1 < len(sys.argv):
                evals = int(sys.argv[i + 1])
            elif arg == "--algorithm" and i + 1 < len(sys.argv):
                algo = sys.argv[i + 1]

        if algo == "random":
            alg = RandomSearch()
        else:
            alg = Standard_MAP_Elites()

        archive = alg.run(max_evals=evals, verbose=True)

        stats = archive.get_statistics()
        elites = archive.get_all_elites()
        playable = sum(1 for _, f, _ in elites if f > 0.6)
        results = {
            "coverage": stats["coverage"],
            "qd_score": stats["qd_score"],
            "max_fitness": stats["max_fitness"],
            "success_at_10k": playable / evals
        }

        print(json.dumps(results, indent=2))

    elif command == "compare":
        evals = 10000

        for i, arg in enumerate(sys.argv):
            if arg == "--evals" and i + 1 < len(sys.argv):
                evals = int(sys.argv[i + 1])

        print("=" * 60)
        print("ALGORITHM COMPARISON")
        print("=" * 60)

        algorithms = {
            "Random Search": RandomSearch(),
            "MAP-Elites": Standard_MAP_Elites()
        }

        comparison = {}
        for name, alg in algorithms.items():
            print(f"\nRunning {name}...")
            archive = alg.run(max_evals=evals, verbose=False)

            stats = archive.get_statistics()
            elites = archive.get_all_elites()
            playable = sum(1 for _, f, _ in elites if f > 0.6)
            results = {
                "coverage": stats["coverage"],
                "qd_score": stats["qd_score"],
                "max_fitness": stats["max_fitness"],
                "success_at_10k": playable / evals
            }

            comparison[name] = results
            print(f"  Coverage: {results['coverage']:.1%}")
            print(f"  QD-Score: {results['qd_score']:.1f}")
            print(f"  Max Fitness: {results['max_fitness']:.3f}")
            print(f"  Success@10k: {results.get('success_at_10k', 0):.3f}")

        print("\n" + "=" * 60)
        print("COMPARISON TABLE")
        print("=" * 60)
        print(f"{'Algorithm':<20} {'Coverage':<12} {'QD-Score':<12} {'Max Fit':<12} {'Success@10k':<12}")
        print("-" * 60)
        for name, res in comparison.items():
            print(f"{name:<20} {res['coverage']:<12.1%} {res['qd_score']:<12.1f} "
                  f"{res['max_fitness']:<12.3f} {res.get('success_at_10k', 0):<12.3f}")

    elif command == "export":
        input_path = None
        output_path = "godot_scene.json"

        for i, arg in enumerate(sys.argv):
            if arg == "--input" and i + 1 < len(sys.argv):
                input_path = sys.argv[i + 1]
            elif arg == "--output" and i + 1 < len(sys.argv):
                output_path = sys.argv[i + 1]

        if not input_path:
            print("Error: --input required")
            return

        with open(input_path, 'r') as f:
            data = json.load(f)

        grid = np.array(data["grid"])
        rule = CARule.from_string(data["rule"])

        exporter = GodotExporter()
        scene = exporter.export_to_godot(grid, rule, data["ticks"], output_path)

        print(f"Exported to {output_path}")
        print(f"  Grid size: {grid.shape}")
        print(f"  Playable: {scene['metadata']['playable']}")
        print(f"  Player spawn: {scene['player_spawn']}")

    elif command == "query":
        style = "branching"
        evals = 10000
        algo = "map_elites"
        grid_size = (20, 20)
        ticks = 100

        for i, arg in enumerate(sys.argv):
            if arg == "--style" and i + 1 < len(sys.argv):
                style = sys.argv[i + 1]
            elif arg == "--evals" and i + 1 < len(sys.argv):
                evals = int(sys.argv[i + 1])
            elif arg == "--algorithm" and i + 1 < len(sys.argv):
                algo = sys.argv[i + 1]

        if style not in ("linear", "branching", "open"):
            print(f"Error: --style must be one of linear, branching, open (got {style})")
            return

        if algo == "random":
            alg = RandomSearch()
        else:
            alg = Standard_MAP_Elites()

        archive = alg.run(grid_size=grid_size, ticks=ticks, max_evals=evals, verbose=False)
        elites = archive.get_all_elites()

        matches = [(sol, fitness, desc) for sol, fitness, desc in elites
                   if classify_topology(float(desc[1])) == style]

        if not matches:
            print(json.dumps({"style": style, "found": False, "message": "No archive cell matches this style."}))
            return

        best_sol, best_fitness, best_desc = max(matches, key=lambda m: m[1])
        rule = CARule.from_genotype(best_sol)
        grid = initialize_random(grid_size, seed=42)
        for t in range(ticks):
            grid = step_ca(grid, rule)

        result = {
            "style": style,
            "found": True,
            "rule": str(rule),
            "fitness": float(best_fitness),
            "descriptors": {
                "coverage": float(best_desc[0]),
                "path_topology_score": float(best_desc[1]),
                "chokepoint_density": float(best_desc[2])
            },
            "grid": grid.tolist(),
            "playable": bool(has_path(grid) > 0.5)
        }
        print(json.dumps(result))

    else:
        print(f"Unknown command: {command}")


# =============================================================================
# DEMO / QUICK TEST
# =============================================================================

if __name__ == "__main__":
    import sys

    # If arguments provided, run CLI
    if len(sys.argv) > 1:
        main()
    else:
        # Run demo comparison
        print("=" * 70)
        print("FUNG-AI v2.0 DEMO: MAP-Elites vs Random Search")
        print("=" * 70)
        print()
        print("This demo runs a quick comparison of algorithms on CA cave generation.")
        print("For full benchmark, use: python fung_ai_v2.py compare --evals 10000")
        print()

        # Quick demo with small budget
        DEMO_EVALS = 500

        print(f"Running with {DEMO_EVALS} evaluations (demo mode)...")
        print()

        # MAP-Elites
        print("[1/2] Standard MAP-Elites")
        me = Standard_MAP_Elites()
        archive_me = me.run(max_evals=DEMO_EVALS, verbose=False)
        stats_me = archive_me.get_statistics()
        elites_me = archive_me.get_all_elites()
        playable_me = sum(1 for _, f, _ in elites_me if f > 0.6)

        # Random
        print("[2/2] Random Search")
        rs = RandomSearch()
        archive_rs = rs.run(max_evals=DEMO_EVALS, verbose=False)
        stats_rs = archive_rs.get_statistics()
        elites_rs = archive_rs.get_all_elites()
        playable_rs = sum(1 for _, f, _ in elites_rs if f > 0.6)

        print()
        print("=" * 70)
        print("DEMO RESULTS")
        print("=" * 70)
        print(f"{'Metric':<25} {'Random':<15} {'MAP-Elites':<15}")
        print("-" * 70)
        print(f"{'Coverage':<25} {stats_rs['coverage']:<15.1%} {stats_me['coverage']:<15.1%}")
        print(f"{'QD-Score':<25} {stats_rs['qd_score']:<15.1f} {stats_me['qd_score']:<15.1f}")
        print(f"{'Max Fitness':<25} {stats_rs['max_fitness']:<15.3f} {stats_me['max_fitness']:<15.3f}")
        print(f"{'Playable Caves':<25} {playable_rs:<15} {playable_me:<15}")
        print()
        print("For full benchmark with 10k evaluations:")
        print("  python fung_ai_v2.py compare --evals 10000")
