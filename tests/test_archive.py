"""
W6: 12 tests for GridArchive and ArchiveCell.
"""

import numpy as np
import pytest

try:
    from fung_ai_v2.archive import GridArchive, ArchiveCell
except ImportError:
    pytest.skip("fung_ai_v2 package not available (archive module)", allow_module_level=True)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_archive(dims=None):
    if dims is None:
        dims = [(0.0, 1.0, 5), (0.0, 1.0, 5), (0.0, 1.0, 5)]
    return GridArchive(dims, alpha=0.5)


def _dummy_solution(seed=0):
    rng = np.random.RandomState(seed)
    return rng.random(18).astype(np.float32)


# ---------------------------------------------------------------------------
# Basic archive state
# ---------------------------------------------------------------------------

def test_archive_starts_empty():
    """A fresh archive has 0% coverage."""
    arch = _make_archive()
    assert arch.coverage() == pytest.approx(0.0)


def test_archive_add_returns_true_on_new():
    """First add to an empty cell returns True."""
    arch = _make_archive()
    sol = _dummy_solution(0)
    desc = np.array([0.1, 0.1, 0.1], dtype=np.float32)
    added = arch.add(sol, fitness=0.5, descriptors=desc)
    assert added is True


def test_archive_add_returns_false_on_worse():
    """Adding a lower-fitness solution to an already-filled cell returns False."""
    arch = _make_archive()
    sol = _dummy_solution(0)
    desc = np.array([0.1, 0.1, 0.1], dtype=np.float32)

    arch.add(sol, fitness=0.8, descriptors=desc)          # fills cell
    result = arch.add(sol, fitness=0.3, descriptors=desc)  # worse — should not replace
    assert result is False


def test_archive_coverage_increases():
    """Coverage fraction increases after filling distinct cells."""
    arch = _make_archive()
    assert arch.coverage() == pytest.approx(0.0)

    arch.add(_dummy_solution(0), fitness=0.5, descriptors=np.array([0.1, 0.1, 0.1], dtype=np.float32))
    arch.add(_dummy_solution(1), fitness=0.6, descriptors=np.array([0.9, 0.9, 0.9], dtype=np.float32))

    assert arch.coverage() > 0.0


# ---------------------------------------------------------------------------
# get_random_elite
# ---------------------------------------------------------------------------

def test_archive_get_random_elite_from_empty_returns_none():
    """Empty archive's get_random_elite returns (None, -inf, None)."""
    arch = _make_archive()
    sol, fitness, desc = arch.get_random_elite()
    assert sol is None
    assert fitness == -np.inf
    assert desc is None


def test_archive_get_random_elite_from_filled():
    """After filling one cell, get_random_elite returns valid (solution, fitness, descriptors)."""
    arch = _make_archive()
    original_sol = _dummy_solution(5)
    desc = np.array([0.2, 0.3, 0.4], dtype=np.float32)
    arch.add(original_sol, fitness=0.75, descriptors=desc)

    sol, fitness, descriptors = arch.get_random_elite()
    assert sol is not None
    assert isinstance(sol, np.ndarray)
    assert sol.shape == (18,)
    assert fitness == pytest.approx(0.75)
    assert descriptors is not None
    assert descriptors.shape == (3,)


# ---------------------------------------------------------------------------
# QD score and statistics
# ---------------------------------------------------------------------------

def test_archive_qd_score_positive():
    """QD score equals the sum of all stored fitnesses (must be > 0 after adds)."""
    arch = _make_archive()
    f1, f2 = 0.4, 0.6
    arch.add(_dummy_solution(0), fitness=f1, descriptors=np.array([0.1, 0.1, 0.1], dtype=np.float32))
    arch.add(_dummy_solution(1), fitness=f2, descriptors=np.array([0.9, 0.9, 0.9], dtype=np.float32))

    assert arch.qd_score() == pytest.approx(f1 + f2, abs=1e-5)


def test_archive_statistics_keys():
    """get_statistics() returns a dict with at minimum the required keys."""
    arch = _make_archive()
    arch.add(_dummy_solution(0), fitness=0.5, descriptors=np.array([0.5, 0.5, 0.5], dtype=np.float32))

    stats = arch.get_statistics()
    required = {"coverage", "qd_score", "max_fitness", "mean_fitness"}
    assert required.issubset(stats.keys()), (
        f"get_statistics() missing keys: {required - stats.keys()}"
    )


# ---------------------------------------------------------------------------
# get_all_elites
# ---------------------------------------------------------------------------

def test_archive_get_all_elites_empty():
    """Empty archive returns an empty list from get_all_elites."""
    arch = _make_archive()
    assert arch.get_all_elites() == []


def test_archive_get_all_elites_filled():
    """Filled archive returns a list of (solution, fitness, descriptors) tuples."""
    arch = _make_archive()
    arch.add(_dummy_solution(0), fitness=0.5, descriptors=np.array([0.1, 0.2, 0.3], dtype=np.float32))
    arch.add(_dummy_solution(1), fitness=0.7, descriptors=np.array([0.8, 0.7, 0.6], dtype=np.float32))

    elites = arch.get_all_elites()
    assert len(elites) >= 1
    for item in elites:
        sol, fit, desc = item
        assert isinstance(sol, np.ndarray)
        assert isinstance(fit, float)
        assert isinstance(desc, np.ndarray)


# ---------------------------------------------------------------------------
# CMA-MAE threshold annealing
# ---------------------------------------------------------------------------

def test_archive_cma_mae_threshold_annealing():
    """Re-adding to a cell with a higher fitness anneals the threshold away from -inf."""
    arch = _make_archive(dims=[(0.0, 1.0, 10), (0.0, 1.0, 10), (0.0, 1.0, 10)])
    desc = np.array([0.05, 0.05, 0.05], dtype=np.float32)
    sol = _dummy_solution(0)

    arch.add(sol, fitness=0.4, descriptors=desc)  # sets threshold = 0.4
    # Retrieve the cell's threshold before second add
    idx = arch._get_index(desc)
    cell = arch.grid[idx]
    threshold_before = cell.threshold

    # Add again with higher fitness — triggers update_threshold
    arch.add(_dummy_solution(1), fitness=0.9, descriptors=desc)
    threshold_after = cell.threshold

    assert threshold_after != threshold_before, (
        "CMA-MAE threshold should anneal after a higher-fitness add"
    )
    assert threshold_after != -np.inf


# ---------------------------------------------------------------------------
# Multi-dimensional archive
# ---------------------------------------------------------------------------

def test_archive_3d_dims():
    """A 3D archive with non-unit dims accepts items and places them correctly."""
    dims = [(0.0, 1.0, 4), (0.0, 1.0, 4), (0.0, 1.0, 4)]
    arch = GridArchive(dims, alpha=0.3)
    sol = _dummy_solution(99)
    desc = np.array([0.5, 0.5, 0.5], dtype=np.float32)

    added = arch.add(sol, fitness=0.6, descriptors=desc)
    assert added is True
    assert arch.coverage() > 0.0

    # The placed cell should appear in get_all_elites
    elites = arch.get_all_elites()
    assert len(elites) == 1
    retrieved_sol, retrieved_fit, _ = elites[0]
    assert np.allclose(retrieved_sol, sol)
    assert retrieved_fit == pytest.approx(0.6)


# ---------------------------------------------------------------------------
# Edge case tests for 100% coverage
# ---------------------------------------------------------------------------

def test_archive_get_statistics_empty():
    """get_statistics() on an empty archive should handle gracefully (line 155)."""
    dims = [(0.0, 1.0, 10), (0.0, 1.0, 10), (0.0, 1.0, 10)]
    arch = GridArchive(dims)

    stats = arch.get_statistics()

    assert stats["coverage"] == 0.0
    assert stats["qd_score"] == 0.0
    assert stats["max_fitness"] == -np.inf
    assert stats["mean_fitness"] == 0.0


def test_archive_cell_threshold_initialization():
    """ArchiveCell.update_threshold initializes threshold from -inf (line 40)."""
    cell = ArchiveCell()
    assert cell.threshold == -np.inf, "New cell should have threshold = -inf"

    # First update should set threshold to the fitness value
    cell.update_threshold(0.8, alpha=0.5)
    assert cell.threshold == 0.8, "First update should set threshold to fitness value"

    # Second update should anneal
    cell.update_threshold(0.9, alpha=0.5)
    expected = 0.5 * 0.8 + 0.5 * 0.9  # (1-alpha)*old + alpha*new
    assert cell.threshold == pytest.approx(expected), "Second update should anneal threshold"
