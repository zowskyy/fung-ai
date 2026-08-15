"""
W5: 18 tests for fitness and descriptor functions.
Tests: has_path, evaluate_ca_rule, compute_descriptors, compute_pattern_entropy,
       compute_pacing_variance, compute_interestingness, classify_topology.
"""

import numpy as np
import pytest

try:
    from fung_ai_v2.ca_engine import CARule
    from fung_ai_v2.fitness import (
        has_path, evaluate_ca_rule, compute_descriptors,
        compute_pattern_entropy, compute_pacing_variance,
        compute_interestingness, classify_topology,
    )
except ImportError:
    pytest.skip("fung_ai_v2 package not available (fitness module)", allow_module_level=True)


# ---------------------------------------------------------------------------
# has_path
# ---------------------------------------------------------------------------

def test_has_path_corridor_grid(corridor_grid):
    """Grid with open column 10 should have path > 0."""
    result = has_path(corridor_grid)
    assert result > 0.0, "Corridor grid has a top-to-bottom path — should return > 0"


def test_has_path_full_grid_returns_zero(full_grid):
    """All-wall grid (all ones) → no passable cells → path score = 0."""
    result = has_path(full_grid)
    assert result == 0.0, "Full wall grid should have no path"


def test_has_path_empty_grid_returns_one():
    """All-floor grid (all zeros) → fully connected → path score = 1.0."""
    g = np.zeros((20, 20), dtype=np.float32)
    result = has_path(g)
    assert result == pytest.approx(1.0), "All-floor grid should have path score 1.0"


def test_has_path_blocked_returns_zero():
    """Grid with a solid horizontal wall through the middle has no top-to-bottom path."""
    g = np.zeros((20, 20), dtype=np.float32)
    g[10, :] = 1.0  # solid wall across the middle row
    result = has_path(g)
    assert result == 0.0, "Solid wall across middle should block all paths"


def test_has_path_return_range():
    """has_path always returns a value in [0.0, 1.0]."""
    rng = np.random.RandomState(0)
    for _ in range(20):
        g = (rng.random((15, 15)) < 0.5).astype(np.float32)
        r = has_path(g)
        assert 0.0 <= r <= 1.0, f"has_path returned {r}, out of [0.0, 1.0]"


# ---------------------------------------------------------------------------
# compute_descriptors
# ---------------------------------------------------------------------------

def test_compute_descriptors_shape(random_grid, b3s23):
    """compute_descriptors returns an ndarray of length 3."""
    desc = compute_descriptors(random_grid, b3s23)
    assert isinstance(desc, np.ndarray)
    assert desc.shape == (3,)


def test_compute_descriptors_range(random_grid, b3s23):
    """All descriptor values are in [0.0, 1.0]."""
    desc = compute_descriptors(random_grid, b3s23)
    assert np.all(desc >= 0.0) and np.all(desc <= 1.0), (
        f"Descriptor values out of [0,1]: {desc}"
    )


def test_compute_descriptors_full_grid_zero_passable(full_grid, b3s23):
    """All-wall grid → topology_score=0, chokepoint_density=0."""
    desc = compute_descriptors(full_grid, b3s23)
    # desc = [coverage, topology_score, chokepoint_density]
    topology_score = float(desc[1])
    chokepoint_density = float(desc[2])
    assert topology_score == pytest.approx(0.0), "No passable cells → topology_score should be 0"
    assert chokepoint_density == pytest.approx(0.0), "No passable cells → chokepoint should be 0"


# ---------------------------------------------------------------------------
# evaluate_ca_rule
# ---------------------------------------------------------------------------

def test_evaluate_ca_rule_returns_tuple(b3s23):
    """evaluate_ca_rule returns a (float, np.ndarray) tuple."""
    result = evaluate_ca_rule(b3s23, (10, 10), seed=1, ticks=10)
    assert isinstance(result, tuple)
    assert len(result) == 2
    fitness, descriptors = result
    assert isinstance(fitness, float)
    assert isinstance(descriptors, np.ndarray)


def test_evaluate_ca_rule_fitness_range(b3s23):
    """Fitness is always in [0.0, 1.0]."""
    fitness, _ = evaluate_ca_rule(b3s23, (15, 15), seed=7, ticks=20)
    assert 0.0 <= fitness <= 1.0, f"Fitness {fitness} out of [0.0, 1.0]"


def test_evaluate_ca_rule_extinction_penalized():
    """A rule with no birth/survival births nothing and kills everything → fitness < 0.05."""
    extinction_rule = CARule(birth=set(), survival=set())
    fitness, _ = evaluate_ca_rule(extinction_rule, (15, 15), seed=3, ticks=5)
    assert fitness < 0.05, (
        f"Extinction rule (all cells die) should have fitness < 0.05, got {fitness}"
    )


# ---------------------------------------------------------------------------
# compute_pattern_entropy
# ---------------------------------------------------------------------------

def test_compute_pattern_entropy_empty_returns_zero():
    """All-dead (no passable cells) grid gives low/zero pattern entropy."""
    passable = np.zeros((20, 20), dtype=bool)
    entropy = compute_pattern_entropy(passable)
    # All patterns are identical (all-zero 3x3), so entropy should be 0
    assert entropy == pytest.approx(0.0), (
        f"Uniform empty passable grid should have entropy ~0, got {entropy}"
    )


def test_compute_pattern_entropy_range():
    """Pattern entropy is always in [0.0, 1.0]."""
    rng = np.random.RandomState(5)
    for _ in range(10):
        passable = rng.random((20, 20)) < 0.5
        e = compute_pattern_entropy(passable)
        assert 0.0 <= e <= 1.0, f"compute_pattern_entropy returned {e} out of [0,1]"


def test_compute_pattern_entropy_uniform_vs_varied():
    """Varied (random) passable mask has higher entropy than a uniform one."""
    uniform = np.zeros((20, 20), dtype=bool)
    rng = np.random.RandomState(12)
    varied = rng.random((20, 20)) < 0.5

    e_uniform = compute_pattern_entropy(uniform)
    e_varied = compute_pattern_entropy(varied)
    assert e_varied > e_uniform, (
        f"Varied mask entropy {e_varied} should exceed uniform mask entropy {e_uniform}"
    )


# ---------------------------------------------------------------------------
# compute_pacing_variance
# ---------------------------------------------------------------------------

def test_compute_pacing_variance_range():
    """compute_pacing_variance always returns [0.0, 1.0]."""
    rng = np.random.RandomState(8)
    for _ in range(10):
        passable = rng.random((20, 20)) < 0.5
        pv = compute_pacing_variance(passable)
        assert 0.0 <= pv <= 1.0, f"compute_pacing_variance returned {pv} out of [0,1]"


# ---------------------------------------------------------------------------
# compute_interestingness
# ---------------------------------------------------------------------------

def test_compute_interestingness_range():
    """compute_interestingness always returns [0.0, 1.0]."""
    rng = np.random.RandomState(9)
    for _ in range(10):
        grid = (rng.random((20, 20)) < 0.5).astype(np.float32)
        score = compute_interestingness(grid)
        assert 0.0 <= score <= 1.0, f"compute_interestingness returned {score} out of [0,1]"


# ---------------------------------------------------------------------------
# classify_topology
# ---------------------------------------------------------------------------

def test_classify_topology_linear():
    """topology_score < 0.33 → 'linear'."""
    assert classify_topology(0.0) == "linear"
    assert classify_topology(0.1) == "linear"
    assert classify_topology(0.32) == "linear"


def test_classify_topology_branching():
    """0.33 <= topology_score < 0.66 → 'branching'; >= 0.66 → 'open'."""
    assert classify_topology(0.33) == "branching"
    assert classify_topology(0.5) == "branching"
    assert classify_topology(0.65) == "branching"
    assert classify_topology(0.66) == "open"
    assert classify_topology(0.8) == "open"
    assert classify_topology(1.0) == "open"


# ---------------------------------------------------------------------------
# Edge case tests for 100% coverage
# ---------------------------------------------------------------------------

def test_compute_pattern_entropy_tiny_grid():
    """Grid smaller than 3x3 should return 0.0 (line 81)."""
    tiny = np.ones((2, 2), dtype=bool)
    result = compute_pattern_entropy(tiny)
    assert result == 0.0, "Tiny grid (<3x3) should return 0.0"


def test_compute_pattern_entropy_single_column():
    """Very narrow grid (1 column, 5 rows) should return 0.0 (line 81)."""
    narrow = np.ones((5, 1), dtype=bool)
    result = compute_pattern_entropy(narrow)
    assert result == 0.0, "Grid with <3 columns should return 0.0"
