"""Emitter interfaces for quality diversity algorithms in fung_ai_v2.

Extracted from fung_ai_v2.py Section 4 (Papers 1-5, 29-30).

Contains:
  - Emitter: Abstract emitter ABC
  - MAP_Elites_Emitter: Standard MAP-Elites emitter with Gaussian mutation
"""

import random
from abc import ABC, abstractmethod
from typing import List

import numpy as np

from .archive import GridArchive


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
                e1, _, _ = archive.get_random_elite()
                e2, _, _ = archive.get_random_elite()
                if e1 is not None and e2 is not None:
                    child = np.where(np.random.random(18) < 0.5, e1, e2)
                    child += np.random.normal(0, self.mutation_std, 18)
                    child = np.clip(child, 0, 1)
                    solutions.append(child)
                else:
                    solutions.append(np.random.random(18))
            else:
                elite, _, _ = archive.get_random_elite()
                if elite is not None:
                    mutant = elite + np.random.normal(0, self.mutation_std, 18)
                    mutant = np.clip(mutant, 0, 1)
                    solutions.append(mutant)
                else:
                    solutions.append(np.random.random(18))
        return solutions

    def tell(self, archive, solutions, fitnesses, descriptors):
        """Update emitter state with evaluation results.

        For pure mutation-based MAP-Elites, this is a no-op beyond counting.
        Adaptive emitters (e.g., CMA-MAE) would update step-size matrices here.
        """
        self.eval_count += len(solutions)
