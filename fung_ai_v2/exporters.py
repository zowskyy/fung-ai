"""Godot 4 exporter for fung_ai_v2.

Extracted from fung_ai_v2.py Section 9 (Papers 16-19).

Bug fixes applied:
  - Bug 2: Non-deterministic enemy spawns fixed. The original used
    np.random.randint(len(largest_region)) with no seed, making enemy spawn
    positions non-reproducible. Fixed by adding an optional `seed` parameter
    to export_to_godot and using np.random.RandomState(seed) for all random
    calls inside the function.

Contains:
  - GodotExporter: Export CA-generated caves to Godot 4 compatible format
"""

import json
from typing import Dict, List, Optional

import numpy as np
from scipy import ndimage

from .ca_engine import CARule
from .fitness import has_path


class GodotExporter:
    """Export CA-generated caves to Godot 4 compatible format.

    Inspired by GameCraft-Bench (2026) and WorldGen (2025) engine integration.
    """

    def __init__(self, tile_size: int = 32):
        self.tile_size = tile_size

    def export_to_godot(
        self,
        grid: np.ndarray,
        rule: CARule,
        ticks: int,
        output_path: str,
        seed: Optional[int] = None,
    ) -> Dict:
        """Generate Godot 4 scene JSON.

        Args:
            grid: CA grid (1=wall, 0=floor).
            rule: CA rule used to generate the grid.
            ticks: Number of CA ticks applied.
            output_path: Path to write the JSON scene file.
            seed: RNG seed for enemy spawn point selection. Use a fixed seed
                  for reproducible exports (Bug 2 fix).

        Exports:
          - TileMapLayer for cave walls/floors
          - NavigationRegion2D for pathfinding
          - Collision shapes for physics
          - Spawn points for player/enemies
        """
        # Bug 2 fix: use a seeded RNG rather than the global np.random state.
        rng = np.random.RandomState(seed)

        h, w = grid.shape

        # Generate tilemap data
        tilemap = []
        for i in range(h):
            for j in range(w):
                tile_type = "wall" if grid[i, j] > 0.5 else "floor"
                tilemap.append({
                    "x": j * self.tile_size,
                    "y": i * self.tile_size,
                    "type": tile_type,
                    "coords": [i, j],
                })

        # Find spawn points (largest empty region)
        passable = 1 - grid
        labeled, num_features = ndimage.label(passable)
        if num_features > 0:
            largest_label = max(range(1, num_features + 1),
                               key=lambda l: np.sum(labeled == l))
            largest_region = np.argwhere(labeled == largest_label)

            # Player spawn: center of largest region
            center = largest_region[len(largest_region) // 2]
            player_spawn = {
                "x": int(center[1]) * self.tile_size + self.tile_size // 2,
                "y": int(center[0]) * self.tile_size + self.tile_size // 2,
            }

            # Enemy spawns: random points in largest region
            # Bug 2 fix: use rng.randint instead of np.random.randint so
            # results are reproducible when seed is provided.
            enemy_spawns = []
            if len(largest_region) > 10:
                for _ in range(min(5, len(largest_region) // 10)):
                    pt = largest_region[rng.randint(len(largest_region))]
                    enemy_spawns.append({
                        "x": int(pt[1]) * self.tile_size + self.tile_size // 2,
                        "y": int(pt[0]) * self.tile_size + self.tile_size // 2,
                    })
        else:
            player_spawn = {"x": w * self.tile_size // 2, "y": h * self.tile_size // 2}
            enemy_spawns = []

        # Navigation polygon (simplified)
        navigation = self._generate_navigation_polygon(grid)

        scene = {
            "version": "4.0",
            "type": "Node2D",
            "name": "CaveLevel",
            "tilemap": tilemap,
            "navigation": navigation,
            "player_spawn": player_spawn,
            "enemy_spawns": enemy_spawns,
            "metadata": {
                "rule": str(rule),
                "ticks": ticks,
                "grid_size": [h, w],
                "tile_size": self.tile_size,
                "playable": bool(has_path(grid) > 0.5),
            },
        }

        with open(output_path, 'w') as f:
            json.dump(scene, f, indent=2)

        return scene

    def _generate_navigation_polygon(self, grid: np.ndarray) -> List[Dict]:
        """Generate simplified navigation polygons from passable regions."""
        passable = 1 - grid
        labeled, num_features = ndimage.label(passable)

        polygons = []
        for label in range(1, num_features + 1):
            region = np.argwhere(labeled == label)
            if len(region) < 10:
                continue

            min_y, min_x = region.min(axis=0)
            max_y, max_x = region.max(axis=0)

            polygons.append({
                "type": "rectangle",
                "x": int(min_x) * self.tile_size,
                "y": int(min_y) * self.tile_size,
                "width": int(max_x - min_x + 1) * self.tile_size,
                "height": int(max_y - min_y + 1) * self.tile_size,
            })

        return polygons
