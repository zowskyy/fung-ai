"""
W6: Tests for environment/biome integration.

classify_biome() is tested directly (no network).
get_environment() integration tests use unittest.mock to avoid live HTTP calls.
"""

import pytest
from unittest.mock import patch, MagicMock

try:
    from fung_ai_v2.environment import classify_biome, get_biome, get_environment
except ImportError:
    pytest.skip("fung_ai_v2 package not available (environment module)", allow_module_level=True)


# ---------------------------------------------------------------------------
# classify_biome — pure function, no network
# ---------------------------------------------------------------------------

def test_desert_hot_dry():
    """Hot and very dry → desert."""
    assert classify_biome(25.0, 100.0) == "desert"


def test_tundra_cold_dry():
    """Cold and dry → tundra."""
    assert classify_biome(-10.0, 150.0) == "tundra"


def test_tundra_cold_wet():
    """Very cold even with moisture → tundra."""
    assert classify_biome(-8.0, 500.0) == "tundra"


def test_tropical_rainforest():
    """Hot and very wet → tropical rainforest."""
    assert classify_biome(25.0, 3000.0) == "tropical_rainforest"


def test_tropical_seasonal_forest():
    """Hot, moderately wet → tropical seasonal forest."""
    assert classify_biome(22.0, 1500.0) == "tropical_seasonal_forest"


def test_boreal_forest_cold_wet():
    """Cold but wet enough for trees → boreal forest."""
    assert classify_biome(1.0, 500.0) == "boreal_forest"


def test_temperate_forest():
    """Mild temperature, moderate precipitation → temperate forest."""
    assert classify_biome(15.0, 900.0) == "temperate_forest"


def test_temperate_grassland():
    """Mild temperature, dry → temperate grassland."""
    assert classify_biome(15.0, 400.0) == "temperate_grassland"


def test_temperate_rainforest():
    """Mild temperature, very wet → temperate rainforest."""
    assert classify_biome(14.0, 2500.0) == "temperate_rainforest"


def test_woodland_shrubland():
    """Hot, intermediate precipitation → woodland/shrubland."""
    assert classify_biome(22.0, 800.0) == "woodland_shrubland"


def test_classify_biome_returns_string():
    """classify_biome always returns a str."""
    result = classify_biome(10.0, 800.0)
    assert isinstance(result, str)
    assert len(result) > 0


def test_classify_biome_boundary_precip():
    """Just above the 250mm boundary shouldn't produce desert for cold climates."""
    result = classify_biome(-8.0, 300.0)
    assert result == "tundra"


# ---------------------------------------------------------------------------
# get_environment — mocked HTTP calls
# ---------------------------------------------------------------------------

_FAKE_WEATHER = {
    "elevation_m": 250.0,
    "wind_speed_kmh": 12.0,
    "wind_gusts_kmh": 20.0,
    "temperature_c": 18.0,
}

_FAKE_CLIMATE = {
    "annual_temp_c": 15.0,
    "annual_precip_mm": 900.0,
}


@pytest.fixture(autouse=True)
def _clear_lru_cache():
    """Clear get_environment's lru_cache between tests."""
    get_environment.cache_clear()
    yield
    get_environment.cache_clear()


def test_get_environment_structure():
    """get_environment returns all expected keys."""
    with patch("fung_ai_v2.environment.get_weather_and_elevation", return_value=_FAKE_WEATHER), \
         patch("fung_ai_v2.environment.get_climate_normals", return_value=_FAKE_CLIMATE), \
         patch("fung_ai_v2.environment.get_settlements", return_value=[]):
        result = get_environment(51.5, -0.1)

    assert "coordinates" in result
    assert "elevation_m" in result
    assert "weather" in result
    assert "biome" in result
    assert "settlements" in result


def test_get_environment_coordinates_echoed():
    """Coordinates in the result match what was passed in."""
    with patch("fung_ai_v2.environment.get_weather_and_elevation", return_value=_FAKE_WEATHER), \
         patch("fung_ai_v2.environment.get_climate_normals", return_value=_FAKE_CLIMATE), \
         patch("fung_ai_v2.environment.get_settlements", return_value=[]):
        result = get_environment(48.85, 2.35)

    assert result["coordinates"]["lat"] == pytest.approx(48.85)
    assert result["coordinates"]["lon"] == pytest.approx(2.35)


def test_get_environment_biome_classification():
    """Biome classification is derived from climate normals (15C, 900mm → temperate_forest)."""
    with patch("fung_ai_v2.environment.get_weather_and_elevation", return_value=_FAKE_WEATHER), \
         patch("fung_ai_v2.environment.get_climate_normals", return_value=_FAKE_CLIMATE), \
         patch("fung_ai_v2.environment.get_settlements", return_value=[]):
        result = get_environment(51.5, -0.1)

    assert result["biome"]["classification"] == "temperate_forest"


def test_get_environment_settlement_passthrough():
    """Settlements list from the sub-call is passed through unchanged."""
    fake_settlement = [{"name": "London", "distance_km": 1.2, "type": "city"}]
    with patch("fung_ai_v2.environment.get_weather_and_elevation", return_value=_FAKE_WEATHER), \
         patch("fung_ai_v2.environment.get_climate_normals", return_value=_FAKE_CLIMATE), \
         patch("fung_ai_v2.environment.get_settlements", return_value=fake_settlement):
        result = get_environment(51.5, -0.1)

    assert result["settlements"] == fake_settlement
