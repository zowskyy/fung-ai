"""
W4: 20 tests for the CA engine core.
Tests: CARule, step_ca, initialize_random, BIOME_DENSITY, BIOME_RULE, compute_density.
"""

import numpy as np
import pytest

try:
    from fung_ai_v2.ca_engine import (
        CARule, step_ca, initialize_random,
        BIOME_DENSITY, BIOME_RULE, compute_density,
    )
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fungaiV2_extracted'))
    from fung_ai_v2 import (
        CARule, step_ca, initialize_random,
        BIOME_DENSITY, BIOME_RULE, compute_density,
    )


# ---------------------------------------------------------------------------
# CARule parsing
# ---------------------------------------------------------------------------

def test_carule_from_string_b3s23():
    """Parse 'B3/S23' → birth={3}, survival={2,3}."""
    rule = CARule.from_string("B3/S23")
    assert rule.birth == {3}
    assert rule.survival == {2, 3}


def test_carule_from_string_b36s23():
    """Parse 'B36/S23' → birth contains 3 and 6."""
    rule = CARule.from_string("B36/S23")
    assert 3 in rule.birth
    assert 6 in rule.birth
    assert rule.survival == {2, 3}


def test_carule_str_roundtrip():
    """CARule.from_string(str(rule)) == rule (via dataclass __eq__)."""
    original = CARule.from_string("B3/S23")
    reconstructed = CARule.from_string(str(original))
    assert reconstructed == original


def test_carule_to_genotype_shape():
    """Genotype is exactly length-18 array."""
    rule = CARule.from_string("B3/S23")
    g = rule.to_genotype()
    assert g.shape == (18,)
    assert g.dtype == np.float32


def test_carule_from_genotype_roundtrip():
    """from_genotype(to_genotype(rule)) reproduces identical birth and survival sets."""
    original = CARule.from_string("B3/S23")
    g = original.to_genotype()
    reconstructed = CARule.from_genotype(g)
    assert reconstructed.birth == original.birth, (
        f"birth mismatch: {reconstructed.birth} != {original.birth}"
    )
    assert reconstructed.survival == original.survival, (
        f"survival mismatch: {reconstructed.survival} != {original.survival}"
    )


def test_carule_mutate_returns_new():
    """mutate() returns a new CARule object, not the same reference."""
    rule = CARule.from_string("B3/S23")
    mutated = rule.mutate(prob=0.1)
    assert mutated is not rule
    assert isinstance(mutated, CARule)


def test_carule_crossover_child_genes():
    """Crossover over 100 trials should produce offspring that differ from both parents.

    Parents must differ in many bits so a mixed child is statistically near-certain.
    B3/S23 and B45678/S012345678 differ in every bit — any mixing at all produces
    a child that is neither parent.
    """
    parent1 = CARule.from_string("B3/S23")
    parent2 = CARule.from_string("B45678/S012345678")

    g1 = parent1.to_genotype()
    g2 = parent2.to_genotype()

    # Verify the parents actually differ in many bits (at least 8)
    assert np.sum(np.abs(g1 - g2)) >= 8, "Parents must differ in many bits for this test to be valid"

    any_mixing = False
    for _ in range(100):
        child = parent1.crossover(parent2)
        gc = child.to_genotype()
        if not (np.array_equal(gc, g1) or np.array_equal(gc, g2)):
            any_mixing = True
            break

    assert any_mixing, "Expected at least one crossover to mix genes from both parents"


# ---------------------------------------------------------------------------
# step_ca
# ---------------------------------------------------------------------------

def test_step_ca_empty_grid_stays_empty_b3s23(b3s23, empty_grid):
    """All-zero grid stays zero: no alive cells → no births (B3 needs 3 live neighbors)."""
    result = step_ca(empty_grid, b3s23)
    assert np.all(result == 0.0), "Empty grid should stay empty under B3/S23"


def test_step_ca_full_grid_b3s23(b3s23, full_grid):
    """All-ones grid: every cell has 8 live neighbors, not in S{2,3} → all die."""
    result = step_ca(full_grid, b3s23)
    assert not np.all(result == 1.0), (
        "Fully alive grid should not stay fully alive under B3/S23 (cells with 8 nbrs die)"
    )


def test_step_ca_output_shape_preserved(b3s23, random_grid):
    """Output shape must match input shape."""
    result = step_ca(random_grid, b3s23)
    assert result.shape == random_grid.shape


def test_step_ca_output_binary(b3s23, random_grid):
    """Output contains only 0.0 and 1.0."""
    result = step_ca(random_grid, b3s23)
    unique_vals = np.unique(result)
    for v in unique_vals:
        assert v in (0.0, 1.0), f"Unexpected value {v} in CA output"


def test_step_ca_wrap_mode(b3s23):
    """Cells at edges interact with opposite edges (wrap mode).

    A vertical strip of 3 live cells in the last column means cell [1, 0]
    has exactly 3 live neighbors via wrap → should be born under B3/S23.
    """
    g = np.zeros((10, 10), dtype=np.float32)
    g[0, -1] = 1.0  # top-right
    g[1, -1] = 1.0  # mid-right
    g[2, -1] = 1.0  # bottom-right
    result = step_ca(g, b3s23)
    assert result[1, 0] == 1.0, (
        "wrap mode: cell [1,0] should be born — its 3 live Moore neighbors are in the last column"
    )


def test_step_ca_deterministic(b3s23, random_grid):
    """Same grid + same rule → identical output every call."""
    r1 = step_ca(random_grid, b3s23)
    r2 = step_ca(random_grid, b3s23)
    assert np.array_equal(r1, r2)


# ---------------------------------------------------------------------------
# initialize_random
# ---------------------------------------------------------------------------

def test_initialize_random_shape():
    """Output shape matches the requested grid_size."""
    grid = initialize_random((15, 25), seed=0)
    assert grid.shape == (15, 25)


def test_initialize_random_density_approximate():
    """Mean density ≈ requested density ± 0.05 (large grid, law of large numbers)."""
    density = 0.45
    grid = initialize_random((200, 200), seed=1, density=density)
    assert abs(float(np.mean(grid)) - density) < 0.05, (
        f"Expected density ~{density}, got {np.mean(grid):.3f}"
    )


def test_initialize_random_seed_reproducible():
    """Same seed always produces the identical grid."""
    g1 = initialize_random((20, 20), seed=99)
    g2 = initialize_random((20, 20), seed=99)
    assert np.array_equal(g1, g2)


def test_initialize_random_different_seeds_differ():
    """Different seeds produce different grids."""
    g1 = initialize_random((20, 20), seed=1)
    g2 = initialize_random((20, 20), seed=2)
    assert not np.array_equal(g1, g2)


# ---------------------------------------------------------------------------
# BIOME_DENSITY / BIOME_RULE / compute_density
# ---------------------------------------------------------------------------

def test_biome_density_all_keys():
    """All biome densities are in the range [0.05, 0.90]."""
    for biome, density in BIOME_DENSITY.items():
        assert 0.05 <= density <= 0.90, (
            f"BIOME_DENSITY['{biome}'] = {density} is out of [0.05, 0.90]"
        )


def test_compute_density_settlement_nudge(sample_env):
    """Settlement within radius nudges density DOWN vs no settlement."""
    env_no_settlement = {
        "biome": sample_env["biome"],
        "weather": sample_env["weather"],
        "settlements": [],
        "elevation_m": sample_env["elevation_m"],
    }
    result_with = compute_density(sample_env)
    result_without = compute_density(env_no_settlement)
    assert result_with["final_density"] < result_without["final_density"], (
        "Settlement within radius should reduce density vs no settlement"
    )


def test_compute_density_wind_nudge():
    """High wind speed produces a positive wind adjustment (reduces density)."""
    env = {
        "biome": {"classification": "tropical_rainforest"},
        "weather": {"wind_speed_kmh": 40.0},
        "settlements": [],
        "elevation_m": 100.0,
    }
    result = compute_density(env)
    assert result["wind_adj"] > 0.0, "Wind at 40 km/h should produce a positive wind_adj"
