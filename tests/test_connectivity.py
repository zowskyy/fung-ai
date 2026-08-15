"""
W5: Tests for connectivity and pathfinding (has_path).
Connectivity functions live in fung_ai_v2.fitness.
"""

import numpy as np
import pytest

try:
    from fung_ai_v2.fitness import has_path
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'fungaiV2_extracted'))
    from fung_ai_v2 import has_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _walls(rows, cols):
    """All-wall grid (1 = wall)."""
    return np.ones((rows, cols), dtype=np.int32)


def _open(rows, cols):
    """All-open grid (0 = passable)."""
    return np.zeros((rows, cols), dtype=np.int32)


def _corridor(rows, cols):
    """Solid grid with one vertical corridor through the center."""
    g = _walls(rows, cols)
    mid = cols // 2
    g[:, mid] = 0
    return g


def _top_blocked(rows, cols):
    """Grid with open interior but solid top row — no connection from top."""
    g = _open(rows, cols)
    g[0, :] = 1
    return g


def _bottom_blocked(rows, cols):
    """Grid with open interior but solid bottom row — no connection to bottom."""
    g = _open(rows, cols)
    g[-1, :] = 1
    return g


# ---------------------------------------------------------------------------
# Return value contracts
# ---------------------------------------------------------------------------

def test_has_path_returns_float():
    """has_path always returns a float."""
    g = _open(10, 10)
    result = has_path(g)
    assert isinstance(result, float)


def test_has_path_range():
    """Result is always in [0.0, 1.0]."""
    g = _open(10, 10)
    assert 0.0 <= has_path(g) <= 1.0
    g2 = _walls(10, 10)
    assert 0.0 <= has_path(g2) <= 1.0


# ---------------------------------------------------------------------------
# Clear positive cases
# ---------------------------------------------------------------------------

def test_open_grid_has_path():
    """All-open grid: full top-to-bottom connection."""
    g = _open(10, 10)
    assert has_path(g) > 0.0


def test_vertical_corridor_has_path():
    """Solid grid with one vertical corridor: path exists."""
    g = _corridor(10, 10)
    assert has_path(g) > 0.0


def test_full_reachability_returns_one():
    """All-open grid: every bottom cell is reachable → score near 1.0."""
    g = _open(10, 10)
    assert has_path(g) == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------------------
# Clear negative cases
# ---------------------------------------------------------------------------

def test_all_walls_no_path():
    """All-wall grid: nothing is passable, no path."""
    g = _walls(10, 10)
    assert has_path(g) == 0.0


def test_top_blocked_no_path():
    """Solid top row: no passable cell touches top edge."""
    g = _top_blocked(10, 10)
    assert has_path(g) == 0.0


def test_bottom_blocked_no_path():
    """Solid bottom row: path can never reach bottom edge."""
    g = _bottom_blocked(10, 10)
    assert has_path(g) == 0.0


def test_disconnected_islands_no_path():
    """Two isolated open regions, neither touching both edges — no top-bottom path."""
    g = _walls(10, 10)
    # Top island (row 1-2, cols 1-3) touches top edge
    g[0:2, 1:4] = 0
    # Bottom island (row 8-9, cols 6-8) touches bottom edge
    g[8:10, 6:9] = 0
    # The two open regions are not connected to each other
    assert has_path(g) == 0.0


# ---------------------------------------------------------------------------
# Partial connectivity
# ---------------------------------------------------------------------------

def test_single_corridor_partial_coverage():
    """One-cell-wide corridor: score < 1.0 on a wide grid (only 1/cols bottom cells reachable)."""
    cols = 20
    g = _corridor(10, cols)
    score = has_path(g)
    assert score > 0.0
    assert score <= 1.0 / cols + 0.01


# ---------------------------------------------------------------------------
# Size invariance
# ---------------------------------------------------------------------------

def test_small_grid():
    """Works on minimum viable grid size."""
    g = _open(5, 5)
    assert has_path(g) > 0.0


def test_tall_narrow_corridor():
    """Tall narrow grid with center corridor."""
    g = _corridor(50, 5)
    assert has_path(g) > 0.0


def test_wide_flat_grid():
    """Wide flat open grid — all bottom cells reachable."""
    g = _open(5, 100)
    assert has_path(g) == pytest.approx(1.0, abs=0.01)
