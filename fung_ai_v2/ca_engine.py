"""Cellular Automata engine for fung_ai_v2.

Extracted from fung_ai_v2.py Section 1 (Papers 6, 7, 8, 26, 27, 28).

Contains:
  - CARule: Birth/Survival rule dataclass with genotype encoding
  - step_ca: One Moore-neighborhood CA step
  - initialize_random: Seeded random grid initialization
  - BIOME_DENSITY: Biome -> initial density mapping
  - BIOME_RULE: Biome -> CA rule string mapping
  - compute_density: Compose biome/settlement/wind signals into final density
"""

from dataclasses import dataclass
from typing import Set, Tuple

import numpy as np
from scipy import ndimage


@dataclass
class CARule:
    """Birth/Survival rule encoding for Conway-like cellular automata.

    From Growing Neural CA (Mordvintsev et al., 2020) and
    Evolution of Spots/Stripes in CA (2025).
    """
    birth: Set[int]
    survival: Set[int]

    def __str__(self):
        b = ''.join(str(x) for x in sorted(self.birth))
        s = ''.join(str(x) for x in sorted(self.survival))
        return f"B{b}/S{s}"

    def to_genotype(self) -> np.ndarray:
        """9-bit binary encoding: [B0..B8, S0..S8]"""
        return np.array(
            [float(i in self.birth) for i in range(9)] +
            [float(i in self.survival) for i in range(9)],
            dtype=np.float32
        )

    @classmethod
    def from_genotype(cls, g: np.ndarray) -> "CARule":
        birth = {i for i in range(9) if g[i] > 0.5}
        survival = {i for i in range(9) if g[i + 9] > 0.5}
        return cls(birth, survival)

    @classmethod
    def from_string(cls, rule_str: str) -> "CARule":
        """Parse B3/S23 format."""
        parts = rule_str.split('/')
        birth = set(int(c) for c in parts[0][1:]) if parts[0].startswith('B') else set()
        survival = set(int(c) for c in parts[1][1:]) if parts[1].startswith('S') else set()
        return cls(birth, survival)

    def mutate(self, prob: float = 0.1) -> "CARule":
        """Bit-flip mutation."""
        g = self.to_genotype()
        mask = np.random.random(18) < prob
        g = np.where(mask, 1 - g, g)
        return CARule.from_genotype(g)

    def crossover(self, other: "CARule") -> "CARule":
        """Uniform crossover."""
        g1 = self.to_genotype()
        g2 = other.to_genotype()
        mask = np.random.random(18) < 0.5
        g = np.where(mask, g1, g2)
        return CARule.from_genotype(g)


def step_ca(grid: np.ndarray, rule: CARule) -> np.ndarray:
    """Execute one CA step with Moore neighborhood.

    Standard Life-like CA update with birth/survival rules.
    """
    kernel = np.array([[1, 1, 1],
                       [1, 0, 1],
                       [1, 1, 1]])
    neighbors = ndimage.convolve(grid.astype(np.int32), kernel, mode='wrap')

    born = np.isin(neighbors, list(rule.birth)) & (grid == 0)
    survive = np.isin(neighbors, list(rule.survival)) & (grid == 1)
    new_grid = np.zeros_like(grid)
    new_grid[born | survive] = 1
    return new_grid


def initialize_random(grid_size: Tuple[int, int], seed: int, density: float = 0.45) -> np.ndarray:
    """Initialize random grid with given alive cell density.

    Returns a float32 array of 0.0 (passable/floor) and 1.0 (wall).
    float32 is intentional — it's the dtype used throughout CA operations.
    """
    rng = np.random.RandomState(seed)
    return (rng.random(grid_size) < density).astype(np.float32)


# Biome -> initial density. Higher-precip/warmer biomes get denser initial
# fill (more terrain to carve caves out of); cold/dry biomes get sparser fill.
BIOME_DENSITY = {
    "tropical_rainforest": 0.60,
    "temperate_rainforest": 0.55,
    "tropical_seasonal_forest": 0.52,
    "temperate_forest": 0.48,
    "boreal_forest": 0.45,
    "woodland_shrubland": 0.40,
    "temperate_grassland": 0.35,
    "desert": 0.20,
    "tundra": 0.15,
}

# Biome -> CA rule. Wet/forested biomes get a more permissive survival set
# (denser, more connected structure); dry/cold biomes get a tighter one
# (sparser, more eroded). Sanity-checked standalone against 50 ticks --
# none go extinct or full-fill.
BIOME_RULE = {
    "tropical_rainforest": "B3/S23",
    "temperate_rainforest": "B3/S23",
    "tropical_seasonal_forest": "B36/S23",
    "temperate_forest": "B36/S23",
    "boreal_forest": "B3/S1234",
    "woodland_shrubland": "B3/S1234",
    "temperate_grassland": "B3/S12345",
    "desert": "B3/S123",
    "tundra": "B3/S12",
}

# Nudge caps, each independent of the other -- neither settlements nor wind
# can outweigh the biome signal (whose own spread is 0.15-0.60).
_SETTLEMENT_ADJ_CAP = 0.15
_SETTLEMENT_RADIUS_KM = 10.0
_WIND_ADJ_CAP = 0.15
_WIND_ADJ_PER_KMH = 0.0025
_DENSITY_MIN = 0.05
_DENSITY_MAX = 0.9


def compute_density(env: dict) -> dict:
    """Compose biome/settlement/wind signals into a final initial density.

    - Settlement within _SETTLEMENT_RADIUS_KM: nudges density DOWN (cleared/
      inhabited land is more open), scaled by inverse distance, capped.
    - Wind speed: nudges density DOWN (wind-scoured terrain is more open),
      linear in km/h, capped.
    - Final value clamped to [_DENSITY_MIN, _DENSITY_MAX] so it can never
      produce a degenerate all-empty or all-full starting grid.
    """
    classification = env["biome"]["classification"]
    base_density = BIOME_DENSITY.get(classification, 0.45)

    settlements = env.get("settlements") or []
    nearest_km = min((s["distance_km"] for s in settlements), default=None)
    settlement_adj = 0.0
    if nearest_km is not None and nearest_km <= _SETTLEMENT_RADIUS_KM:
        settlement_adj = _SETTLEMENT_ADJ_CAP * (1 - nearest_km / _SETTLEMENT_RADIUS_KM)
        settlement_adj = min(_SETTLEMENT_ADJ_CAP, settlement_adj)

    wind_kmh = env.get("weather", {}).get("wind_speed_kmh") or 0.0
    wind_adj = min(_WIND_ADJ_CAP, wind_kmh * _WIND_ADJ_PER_KMH)

    final_density = base_density - settlement_adj - wind_adj
    final_density = max(_DENSITY_MIN, min(_DENSITY_MAX, final_density))

    return {
        "classification": classification,
        "base_density": base_density,
        "nearest_settlement_km": nearest_km,
        "settlement_adj": round(settlement_adj, 4),
        "wind_kmh": wind_kmh,
        "wind_adj": round(wind_adj, 4),
        "final_density": round(final_density, 4),
    }
