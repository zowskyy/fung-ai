# Environment Data Pipeline

A plain, importable Python module that turns a `(lat, lon)` coordinate into a
real environmental snapshot: live weather, elevation, a Whittaker biome
classification, and nearby named settlements. No HTTP server — the only
consumer today is `fungaiV2_extracted/fung_ai_v2.py`, in the same process.

## Layout

```
fung.us/
  env_pipeline/
    __init__.py
    environment.py   # get_environment(lat, lon) -> dict
    cache.py          # JSON-file-backed cache with TTLs
    _cache.json        # created on first run, gitignore-worthy
  requirements.txt    # httpx (everything else is stdlib)
  ENV_PIPELINE.md      # this file
```

## Usage

```python
from env_pipeline.environment import get_environment

snapshot = get_environment(10.4631, -84.7033)
```

Returns:

```python
{
  "coordinates": {"lat": 10.4631, "lon": -84.7033},
  "elevation_m": 1625.0,
  "weather": {"wind_speed_kmh": 16.7, "wind_gusts_kmh": 55.8, "temperature_c": 17.3},
  "biome": {"classification": "temperate_rainforest", "annual_temp_c": 16.2, "annual_precip_mm": 3727.6},
  "settlements": [{"name": "La Fortuna", "distance_km": 6.5, "type": "village", "population": 17000}, ...]
}
```

## Data sources

- **Weather + elevation** — Open-Meteo Forecast API (`api.open-meteo.com/v1/forecast`).
  Live current conditions plus the model's elevation for the point, in one call.
- **Climate normals** — Open-Meteo **Archive** API (`archive-api.open-meteo.com/v1/archive`),
  not the dedicated Climate API. **Deviation from the original plan, documented here
  on purpose:** the Climate API requires picking one or more downscaled climate
  models (CMCC_CM2_VHR4, MRI_AGCM3_2_S, etc.) and stitching decades of monthly
  output together — real config-surface growth for a pass that's explicitly trying
  to avoid a config system. The Archive API instead returns daily
  `temperature_2m_mean` / `precipitation_sum` for the most recently completed
  calendar year at the point, which is averaged/summed into an annual figure. It's
  one recent year rather than a 30-year normal, so a single unusual year (drought,
  El Niño) will skew it — acceptable for classifying a biome category, not for
  scientific climatology. Noted as a future upgrade if this proves too noisy.
- **Biome** — computed locally via `classify_biome(temp_c, precip_mm)`, a Whittaker
  diagram approximation (see below). No extra network call.
- **Settlements** — OpenStreetMap Overpass API (`overpass-api.de/api/interpreter`),
  POSTed Overpass QL querying `place` nodes tagged `city`/`town`/`village` within a
  bounding circle (default 25km) around the point. Overpass rejects requests
  without a `User-Agent` header (returns HTTP 406) — `_get_json` always sends one.
  Overpass is a shared public instance; if it's unavailable, `get_settlements`
  degrades to an empty list rather than failing the whole snapshot, since
  settlements are informational-only.

Every external call goes through one shared `_get_json(url, params=None, data=None,
method="GET")` helper in `environment.py`, with a single retry on failure.

## Whittaker biome classification

`classify_biome(temp_c, precip_mm)` buckets mean annual temperature and annual
precipitation into one of nine categories: `tropical_rainforest`,
`tropical_seasonal_forest`, `desert`, `temperate_grassland`, `temperate_forest`,
`temperate_rainforest`, `boreal_forest`, `tundra`, `woodland_shrubland`. It follows
the general shape of the classic Whittaker diagram (hot+wet -> rainforest,
cold+dry -> tundra, hot+dry -> desert) but the thresholds are hand-picked, not
digitized from the original diagram — directionally correct, not
survey-grade. It only looks at temperature and precipitation, not latitude or
seasonality, so points like a tropical-latitude mountain peak (cold because of
elevation, technically a cloud forest) can land in a "temperate" bucket purely
because the numbers match that box. This is the tradeoff called out in the
plan: no ecoregion-level place names (WWF Terrestrial Ecoregions), just a
biome category, in exchange for not needing GDAL/Fiona/geopandas on Windows.

## Caching

`cache.py` is a single JSON file (`env_pipeline/_cache.json`) storing
`{key: {ts, ttl_s, value}}`. Three TTL constants, no config system:

- `TTL_WEATHER_S` = 15 minutes
- `TTL_STATIC_S` (elevation/climate/biome) = ~1 year ("effectively permanent")
- `TTL_SETTLEMENTS_S` = 24 hours

This is the cross-process cache. `get_environment` itself is also wrapped in
`functools.lru_cache`, which memoizes repeat calls within a single running
process (no disk hit at all for a second call in the same run).

## Integration with `fung_ai_v2.py`

`generate --lat <lat> --lon <lon>` (both optional) calls `get_environment`
directly (plain function call, no network hop beyond what `get_environment`
itself does) and maps `biome.classification` onto the density argument
already accepted by `initialize_random()`:

| biome | density |
|---|---|
| tropical_rainforest | 0.60 |
| temperate_rainforest | 0.55 |
| tropical_seasonal_forest | 0.52 |
| temperate_forest | 0.48 |
| boreal_forest | 0.45 |
| woodland_shrubland | 0.40 |
| temperate_grassland | 0.35 |
| desert | 0.20 |
| tundra | 0.15 |

Without `--lat`/`--lon`, density falls back to the original default (0.45).

Wind speed and settlement proximity **are** wired into density (as of this
change — previously informational-only). `compute_density(env)` in
`fung_ai_v2.py` composes the final density from three signals:

```
final_density = clamp(base_density - settlement_adj - wind_adj, 0.05, 0.9)
```

- `base_density` — the biome table above.
- `settlement_adj` — if the nearest settlement (from `get_settlements`'s
  `distance_km`) is within 10km, subtract `0.15 * (1 - distance_km / 10)`,
  capped at 0.15. Closer settlements push density down more (inhabited/
  cleared land is more open); beyond 10km there's no adjustment. This models
  land use, not simulating it — a coarse nudge, not a claim about actual
  clearing.
- `wind_adj` — subtract `wind_speed_kmh * 0.0025`, capped at 0.15. Windier
  points get sparser starting grids (wind-scoured terrain reads as more
  open).
- Both adjustments are capped independently at 0.15 so neither can swamp the
  biome signal (whose own range across the table is 0.15-0.60); worst case
  combined nudge is 0.30.
- The final clamp to `[0.05, 0.9]` is a hard backstop so no combination of
  inputs can produce a degenerate all-empty or all-full starting grid,
  regardless of the biome/settlement/wind combination.

`generate`'s `[env]` trace lines print every term of this calculation
(`base_density`, `settlement_adj` with the nearest distance used,
`wind_adj` with the wind speed used, and the resulting `final_density`) so
the composition is traceable from the CLI output, not a black box.

This is still a one-shot static generator, not a "living dungeon" — the
adjustments are a fixed function of the environment snapshot at generation
time, not a live simulation loop. Real-time environmental effects (weather
changing over a running session, etc.) remain out of scope, as before.

### Multi-biome tiles (`--multi-biome`)

`generate --lat <lat> --lon <lon> --multi-biome` treats the given coordinate
as the center of a 3x3 grid of sub-regions, each offset ~0.5 degrees
(~50km) in lat/lon. It calls `get_environment` once per sub-region (9 calls
total, cheap thanks to the existing cache), looks up a CA rule per
sub-region's biome classification via the `BIOME_RULE` table (next to
`BIOME_DENSITY` in `fung_ai_v2.py`), computes that sub-region's density via
the same `compute_density()` formula above, simulates a `width/3 x height/3`
tile independently for `--ticks` generations, and stitches the 9 tiles into
one composite grid with no blending — a visible seam at biome boundaries is
expected and left as-is. `--width`/`--height` are rounded down to the
nearest multiple of 3 if not already divisible, with a stderr note when this
happens. The JSON output adds `"multi_biome": true` and a `tiles` array (one
entry per sub-region: row/col, lat/lon, biome, rule, and density terms) so
the composition is traceable. Requires both `--lat` and `--lon`; errors
clearly if only one or neither is given.

Note on reading the result: `density_used` sets the *initial* random grid's
fill fraction, which does scale monotonically with the biome table above.
The CA engine's own B3/S23 Life-like update rule is chaotic, though — final
coverage after 50 ticks does not track initial density linearly (this is a
pre-existing property of the CA engine, unrelated to this pipeline). Compare
initial density (`density_used` in the output) across runs to see the biome
effect directly; final `coverage` reflects 50 generations of CA dynamics on
top of that, which is a separate and much noisier signal.

## Future upgrades (explicitly out of scope now)

- HTTP server (FastAPI/uvicorn) once a non-Python consumer (Godot) needs one.
- True ecoregion-level biome data via WWF Terrestrial Ecoregions, if the
  Whittaker approximation proves too coarse.
- Real-time (not one-shot) environmental effects, as part of future
  "living dungeon" runtime work — wind and settlements are now wired into
  initial density (see above), but only as a snapshot at generation time.
- Real multi-decade climate normals via the Climate API, if the one-year
  Archive API proxy proves too noisy.
