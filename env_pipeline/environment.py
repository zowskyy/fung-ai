"""Live environment data pipeline: weather, elevation, biome, settlements.

Plain functions, no server, no schema/ABC layer. `get_environment(lat, lon)`
is the single entry point other code should import.

Data sources (all free, no API key):
  - Open-Meteo Forecast API  -> live weather + elevation
  - Open-Meteo Archive API   -> a recent full year of daily data, used as a
    lightweight stand-in for long-run climate normals (see ENV_PIPELINE.md
    for why this was chosen over the dedicated Climate API)
  - Whittaker biome classification -> derived from the above, no extra call
  - OpenStreetMap Overpass API -> nearest named settlements

Every external call goes through the one shared `_get_json()` helper.
"""
import functools
import math
import time

import httpx

from .cache import (
    TTL_SETTLEMENTS_S,
    TTL_STATIC_S,
    TTL_WEATHER_S,
    cache_get,
    cache_set,
)

_HTTP_TIMEOUT = 15.0
_HTTP_HEADERS = {"User-Agent": "fung-us-env-pipeline/1.0"}

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

_DEFAULT_SETTLEMENT_RADIUS_KM = 25


# ---------------------------------------------------------------------------
# Shared HTTP helper (one retry, plain requests/JSON, no retry framework)
# ---------------------------------------------------------------------------

def _get_json(url: str, params: dict = None, data: dict = None, method: str = "GET") -> dict:
    """Fetch `url` and return parsed JSON. One retry on failure."""
    last_exc = None
    for attempt in range(2):
        try:
            if method == "POST":
                resp = httpx.post(url, data=data, headers=_HTTP_HEADERS, timeout=_HTTP_TIMEOUT)
            else:
                resp = httpx.get(url, params=params, headers=_HTTP_HEADERS, timeout=_HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(1)
    raise RuntimeError(f"Request to {url} failed after retry: {last_exc}")


def _round_key(lat: float, lon: float) -> str:
    return f"{round(lat, 4)},{round(lon, 4)}"


# ---------------------------------------------------------------------------
# Weather + elevation (live, cached 15 min)
# ---------------------------------------------------------------------------

def get_weather_and_elevation(lat: float, lon: float) -> dict:
    key = f"weather:{_round_key(lat, lon)}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    raw = _get_json(FORECAST_URL, params={
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,wind_speed_10m,wind_gusts_10m",
        "wind_speed_unit": "kmh",
        "timezone": "UTC",
    })
    current = raw.get("current", {})
    result = {
        "elevation_m": raw.get("elevation"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "wind_gusts_kmh": current.get("wind_gusts_10m"),
        "temperature_c": current.get("temperature_2m"),
    }
    cache_set(key, result, TTL_WEATHER_S)
    return result


# ---------------------------------------------------------------------------
# Climate normals (proxy: most recent full calendar year of daily data,
# cached ~permanently since this changes only year to year)
# ---------------------------------------------------------------------------

def get_climate_normals(lat: float, lon: float) -> dict:
    key = f"climate:{_round_key(lat, lon)}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    # Most recently completed calendar year, so the archive API always has
    # full data available regardless of when this runs.
    year = time.gmtime().tm_year - 1
    raw = _get_json(ARCHIVE_URL, params={
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": "temperature_2m_mean,precipitation_sum",
        "timezone": "UTC",
    })
    daily = raw.get("daily", {})
    temps = [t for t in daily.get("temperature_2m_mean", []) if t is not None]
    precips = [p for p in daily.get("precipitation_sum", []) if p is not None]

    annual_temp_c = round(sum(temps) / len(temps), 1) if temps else None
    annual_precip_mm = round(sum(precips), 1) if precips else None

    result = {"annual_temp_c": annual_temp_c, "annual_precip_mm": annual_precip_mm}
    cache_set(key, result, TTL_STATIC_S)
    return result


# ---------------------------------------------------------------------------
# Whittaker biome classification
# ---------------------------------------------------------------------------

def classify_biome(temp_c: float, precip_mm: float) -> str:
    """Classify a biome from mean annual temperature (C) and annual
    precipitation (mm), following the standard Whittaker diagram shape.
    Not scientifically exact at the boundaries -- directionally correct
    (hot+wet -> rainforest, cold+dry -> tundra, hot+dry -> desert, etc).
    """
    if precip_mm < 250:
        return "tundra" if temp_c < 5 else "desert"

    if temp_c < -5:
        return "tundra"

    if temp_c < 3:
        return "tundra" if precip_mm < 400 else "boreal_forest"

    if temp_c < 12:
        if precip_mm < 600:
            return "temperate_grassland"
        if precip_mm < 1500:
            return "boreal_forest" if temp_c < 6 else "temperate_forest"
        return "temperate_rainforest"

    if temp_c < 20:
        if precip_mm < 600:
            return "temperate_grassland"
        if precip_mm < 2000:
            return "temperate_forest"
        return "temperate_rainforest"

    # temp_c >= 20 (hot)
    if precip_mm < 1000:
        return "woodland_shrubland"
    if precip_mm < 2000:
        return "tropical_seasonal_forest"
    return "tropical_rainforest"


def get_biome(lat: float, lon: float) -> dict:
    normals = get_climate_normals(lat, lon)
    temp_c, precip_mm = normals["annual_temp_c"], normals["annual_precip_mm"]
    classification = (
        classify_biome(temp_c, precip_mm) if temp_c is not None and precip_mm is not None else "unknown"
    )
    return {
        "classification": classification,
        "annual_temp_c": temp_c,
        "annual_precip_mm": precip_mm,
    }


# ---------------------------------------------------------------------------
# Settlements (OpenStreetMap Overpass, cached 24h)
# ---------------------------------------------------------------------------

def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def get_settlements(lat: float, lon: float, radius_km: float = _DEFAULT_SETTLEMENT_RADIUS_KM) -> list:
    key = f"settlements:{_round_key(lat, lon)}:{radius_km}"
    cached = cache_get(key)
    if cached is not None:
        return cached

    radius_m = int(radius_km * 1000)
    query = (
        "[out:json][timeout:25];"
        f'node["place"~"^(city|town|village)$"](around:{radius_m},{lat},{lon});'
        "out body;"
    )
    try:
        raw = _get_json(OVERPASS_URL, data={"data": query}, method="POST")
    except RuntimeError:
        # Overpass is a shared public instance and occasionally unavailable;
        # settlements are informational-only, so degrade to an empty list
        # rather than failing the whole snapshot.
        cache_set(key, [], TTL_SETTLEMENTS_S)
        return []

    settlements = []
    for el in raw.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        entry = {
            "name": name,
            "distance_km": round(_haversine_km(lat, lon, el["lat"], el["lon"]), 1),
            "type": tags.get("place"),
        }
        if "population" in tags:
            try:
                entry["population"] = int(tags["population"])
            except ValueError:
                pass
        settlements.append(entry)

    settlements.sort(key=lambda s: s["distance_km"])
    cache_set(key, settlements, TTL_SETTLEMENTS_S)
    return settlements


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=256)
def get_environment(lat: float, lon: float, settlement_radius_km: float = _DEFAULT_SETTLEMENT_RADIUS_KM) -> dict:
    """Aggregate a full environmental snapshot for (lat, lon).

    Cheap to call repeatedly within one process (lru_cache); cheap to call
    across separate `python` invocations too, via cache.py's on-disk cache.
    """
    weather = get_weather_and_elevation(lat, lon)
    biome = get_biome(lat, lon)
    settlements = get_settlements(lat, lon, settlement_radius_km)

    return {
        "coordinates": {"lat": lat, "lon": lon},
        "elevation_m": weather["elevation_m"],
        "weather": {
            "wind_speed_kmh": weather["wind_speed_kmh"],
            "wind_gusts_kmh": weather["wind_gusts_kmh"],
            "temperature_c": weather["temperature_c"],
        },
        "biome": biome,
        "settlements": settlements,
    }
