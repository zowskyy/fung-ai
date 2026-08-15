import pytest
import numpy as np

# ---------------------------------------------------------------------------
# Import helpers — try package first, fall back to monolithic source file
# ---------------------------------------------------------------------------

def _import_carule():
    from fung_ai_v2.ca_engine import CARule
    return CARule


@pytest.fixture
def b3s23():
    """Standard Conway-Life-like rule."""
    CARule = _import_carule()
    return CARule.from_string("B3/S23")


@pytest.fixture
def b36s23():
    """Maze-like rule."""
    CARule = _import_carule()
    return CARule.from_string("B36/S23")


@pytest.fixture
def empty_grid():
    return np.zeros((20, 20), dtype=np.float32)


@pytest.fixture
def full_grid():
    return np.ones((20, 20), dtype=np.float32)


@pytest.fixture
def random_grid():
    rng = np.random.RandomState(42)
    return (rng.random((20, 20)) < 0.45).astype(np.float32)


@pytest.fixture
def small_grid():
    """5x5 grid for fast tests."""
    rng = np.random.RandomState(7)
    return (rng.random((5, 5)) < 0.45).astype(np.float32)


@pytest.fixture
def corridor_grid():
    """Grid with a guaranteed top-to-bottom corridor for path tests."""
    g = np.ones((20, 20), dtype=np.float32)
    g[:, 10] = 0  # Column 10 is passable
    return g


@pytest.fixture
def sample_env():
    return {
        "biome": {"classification": "tropical_rainforest", "annual_temp_c": 27.0, "annual_precip_mm": 2500.0},
        "weather": {"wind_speed_kmh": 10.0},
        "settlements": [{"name": "Test City", "distance_km": 5.0}],
        "elevation_m": 100.0,
    }
