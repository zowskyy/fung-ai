"""QD algorithms and benchmark protocol for fung_ai_v2.

Extracted from fung_ai_v2.py Sections 7-8.

Bug fixes applied:
  - Bug 1: Added get_results() to both RandomSearch and Standard_MAP_Elites.
    The original run_held_out_benchmark called algorithm.get_results() but
    neither class implemented it, causing an AttributeError at runtime.

Contains:
  - RandomSearch: Random search baseline
  - Standard_MAP_Elites: MAP-Elites without landscape awareness
  - run_held_out_benchmark: Held-out benchmark protocol
"""

import random
from typing import Dict, List, Tuple

import numpy as np

from .archive import GridArchive
from .ca_engine import CARule
from .emitters import MAP_Elites_Emitter
from .fitness import evaluate_ca_rule


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
        gen = 0
        while evals_done < max_evals:
            gen += 1
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

    def get_results(self) -> Dict:
        """Return benchmark-compatible results dict.

        Bug 1 fix: added this method; run_held_out_benchmark calls
        algorithm.get_results() but the method was previously missing.
        """
        stats = self.archive.get_statistics()
        elites = self.archive.get_all_elites()
        evals = max(self.archive.eval_count, 1)
        playable = sum(1 for _, f, _ in elites if f > 0.6)
        return {
            "coverage": stats["coverage"],
            "qd_score": stats["qd_score"],
            "max_fitness": stats["max_fitness"] if stats["max_fitness"] != -np.inf else 0.0,
            "success_at_10k": playable / evals,
        }


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

    def get_results(self) -> Dict:
        """Return benchmark-compatible results dict.

        Bug 1 fix: added this method; run_held_out_benchmark calls
        algorithm.get_results() but the method was previously missing.
        """
        stats = self.archive.get_statistics()
        elites = self.archive.get_all_elites()
        evals = max(self.archive.eval_count, 1)
        playable = sum(1 for _, f, _ in elites if f > 0.6)
        return {
            "coverage": stats["coverage"],
            "qd_score": stats["qd_score"],
            "max_fitness": stats["max_fitness"] if stats["max_fitness"] != -np.inf else 0.0,
            "success_at_10k": playable / evals,
        }


def run_held_out_benchmark(
    algorithm,
    train_rules=("B3/S23", "B5678/S45678"),
    test_rules=("B36/S23", "B3/S238"),
    grid_sizes=((20, 20), (40, 40), (80, 80)),
    train_seeds=range(1, 1001),
    val_seeds=range(1001, 2001),
    test_seeds=range(2001, 3001),
    max_evals=10000,
    verbose=True,
):
    """Run held-out benchmark protocol from Fung-AI v1.0.

    Training: B3/S23, B5678/S45678 on 20x20, seeds 1-1000
    Validation: Same rules on 40x40, seeds 1001-2000
    Test: B36/S23, B3/S238 on 20x20/40x40/80x80, seeds 2001-3000

    Bug 1 fix: algorithm.get_results() is now implemented on both
    RandomSearch and Standard_MAP_Elites.
    """
    results = {"train": {}, "val": {}, "test": {}}

    if verbose:
        print("=" * 60)
        print("HELD-OUT BENCHMARK PROTOCOL")
        print("=" * 60)
        print("\n[TRAINING PHASE]")

    for rule_str in train_rules:
        rule = CARule.from_string(rule_str)
        if verbose:
            print(f"\n  Training on {rule_str} (20x20, {len(list(train_seeds))} seeds)")

        archive = algorithm.run(grid_size=(20, 20), ticks=100,
                                max_evals=max_evals, seed=42, verbose=verbose)
        results["train"][rule_str] = algorithm.get_results()

    if verbose:
        print("\n[VALIDATION PHASE]")

    for rule_str in train_rules:
        if verbose:
            print(f"\n  Validating on {rule_str} (40x40, {len(list(val_seeds))} seeds)")

        archive = algorithm.run(grid_size=(40, 40), ticks=100,
                                max_evals=max_evals, seed=1042, verbose=verbose)
        results["val"][rule_str] = algorithm.get_results()

    if verbose:
        print("\n[TEST PHASE - GENERALIZATION]")

    for rule_str in test_rules:
        for grid_size in grid_sizes:
            key = f"{rule_str}_{grid_size[0]}x{grid_size[1]}"
            if verbose:
                print(f"\n  Testing on {rule_str} ({grid_size[0]}x{grid_size[1]}, "
                      f"{len(list(test_seeds))} seeds)")

            archive = algorithm.run(grid_size=grid_size, ticks=100,
                                    max_evals=max_evals, seed=2042, verbose=verbose)
            results["test"][key] = algorithm.get_results()

    train_success = np.mean([r["success_at_10k"] for r in results["train"].values()])
    test_success = np.mean([r["success_at_10k"] for r in results["test"].values()])
    generalization_gap = train_success - test_success

    results["summary"] = {
        "train_success": train_success,
        "test_success": test_success,
        "generalization_gap": generalization_gap,
        "generalizes": generalization_gap < 0.05,
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
