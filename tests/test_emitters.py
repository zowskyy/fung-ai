"""
Emitter tests for 100% coverage (reset, edge cases).
"""

import numpy as np
import pytest

try:
    from fung_ai_v2.emitters import Emitter, MAP_Elites_Emitter
    from fung_ai_v2.archive import GridArchive
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fungaiV2_extracted'))
    from fung_ai_v2 import Emitter, MAP_Elites_Emitter, GridArchive


def test_emitter_reset():
    """Emitter.reset() clears eval_count (line 42)."""
    emitter = MAP_Elites_Emitter()

    # Simulate some evaluations
    emitter.eval_count = 100

    # Reset should clear eval_count
    emitter.reset()
    assert emitter.eval_count == 0, "reset() should set eval_count to 0"


def test_map_elites_ask_empty_archive():
    """MAP_Elites_Emitter.ask() handles empty archive gracefully (line 68)."""
    dims = [(0.0, 1.0, 10), (0.0, 1.0, 10), (0.0, 1.0, 10)]
    archive = GridArchive(dims)
    emitter = MAP_Elites_Emitter()

    # Ask for solutions from an empty archive
    solutions = emitter.ask(archive, batch_size=5)

    # Should return 5 random solutions (line 68: fallback when no elites exist)
    assert len(solutions) == 5
    assert all(isinstance(sol, np.ndarray) for sol in solutions)
    assert all(sol.shape == (18,) for sol in solutions)
    assert all(np.all(sol >= 0.0) and np.all(sol <= 1.0) for sol in solutions)


def test_map_elites_ask_single_elite():
    """MAP_Elites_Emitter.ask() mutates single elite when archive has 1 cell."""
    from fung_ai_v2.ca_engine import CARule
    from fung_ai_v2.fitness import evaluate_ca_rule

    dims = [(0.0, 1.0, 10), (0.0, 1.0, 10), (0.0, 1.0, 10)]
    archive = GridArchive(dims)
    emitter = MAP_Elites_Emitter()

    # Add one elite to the archive
    rule = CARule.from_string("B3/S23")
    sol = rule.to_genotype()
    fitness, desc = evaluate_ca_rule(rule, (20, 20), seed=42, ticks=50)
    archive.add(sol, fitness, desc)

    # Ask for solutions — should mutate the single elite
    solutions = emitter.ask(archive, batch_size=3)
    assert len(solutions) == 3
    # At least one should not be identical to the original elite (high probability)
    differences = [not np.allclose(s, sol) for s in solutions]
    assert any(differences), "Mutations should produce some variation"
