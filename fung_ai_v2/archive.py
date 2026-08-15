"""QD archive data structures for fung_ai_v2.

Extracted from fung_ai_v2.py Section 3 (Papers 1-4).

Synthesis of:
  - MAP-Elites (2015) grid structure
  - CMA-MAE (Fontaine et al., 2023) annealing thresholds
  - Dominated Novelty Search (Bahlous-Boldi et al., 2025) density tracking

Contains:
  - ArchiveCell: single archive cell with CMA-MAE annealing threshold
  - GridArchive: N-dimensional grid-based archive
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np


@dataclass
class ArchiveCell:
    """Single cell in the QD archive with CMA-MAE annealing threshold.

    From CMA-MAE (Fontaine et al., 2023): maintains acceptance threshold t_e
    that anneals over time based on archive learning rate alpha.
    From Dominated Novelty Search (Bahlous-Boldi et al., 2025): tracks
    visit_count for density estimation without requiring rho_min parameter.
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
            d = np.clip(descriptors[i], d_min, d_max)
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

        improvement = fitness - cell.threshold

        if cell.elite is None:
            cell.elite = solution.copy()
            cell.fitness = fitness
            cell.threshold = fitness
            cell.last_updated = self.generation
            self.filled_count += 1
            return True
        elif improvement > 0:
            cell.elite = solution.copy()
            cell.fitness = fitness
            cell.last_updated = self.generation
            cell.update_threshold(fitness, self.alpha)
            return True
        else:
            cell.update_threshold(fitness, self.alpha * 0.1)
            return False

    def get_random_elite(self) -> Tuple[np.ndarray, float, np.ndarray]:
        """Sample random elite from filled cells."""
        filled = [(idx, self.grid[idx]) for idx in np.ndindex(self.shape)
                  if self.grid[idx].elite is not None]
        if not filled:
            return None, -np.inf, None
        idx, cell = random.choice(filled)
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
                def _descriptor_i(i):
                    min_val, max_val, num_bins = self.dims[i]
                    bin_width = (max_val - min_val) / num_bins
                    return min_val + (idx[i] + 0.5) * bin_width
                descriptors = np.array([
                    _descriptor_i(i) for i in range(self.num_dims)
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
            "eval_count": self.eval_count,
        }
