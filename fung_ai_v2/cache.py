"""JSON-file-backed cache with TTLs for fung_ai_v2 environment pipeline.

One JSON file on disk (`_cache.json`, next to this module) holds every cached
entry, keyed by an arbitrary string. Each entry stores the value plus the
wall-clock time it was written; `cache_get` reports a miss once the entry's
TTL has elapsed. This is the *cross-run* cache (survives between separate
`python` invocations); `functools.lru_cache` in environment.py handles
repeat calls made within a single process.

No config system: the three TTLs callers need are just constants below.
"""
import json
import threading
import time
from pathlib import Path

# Cache file lives next to this module — uses pathlib, no hardcoded paths.
CACHE_FILE = Path(__file__).parent / "_cache.json"

TTL_WEATHER_S = 15 * 60                # weather changes fast: 15 minutes
TTL_STATIC_S = 365 * 24 * 60 * 60      # elevation/climate/biome: effectively permanent (~1 year)
TTL_SETTLEMENTS_S = 24 * 60 * 60       # settlements: 24 hours

_lock = threading.Lock()


def _load() -> dict:
    if not CACHE_FILE.exists():
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    tmp_path = CACHE_FILE.with_suffix(".json.tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    tmp_path.replace(CACHE_FILE)


def cache_get(key: str):
    """Return the cached value for `key`, or None on a miss/expired entry."""
    with _lock:
        entry = _load().get(key)
    if entry is None:
        return None
    if time.time() - entry["ts"] > entry["ttl_s"]:
        return None
    return entry["value"]


def cache_set(key: str, value, ttl_s: float) -> None:
    """Store `value` under `key` with the given TTL in seconds."""
    with _lock:
        data = _load()
        data[key] = {"ts": time.time(), "ttl_s": ttl_s, "value": value}
        _save(data)
