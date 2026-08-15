"""CLI entry point for fung_ai_v2.

Extracted from fung_ai_v2.py Section 10.

Bug fixes applied:
  - Bug 3: No CLI input validation. Args previously went straight to int()
    with no error handling. Now wrapped in try/except with descriptive error
    messages, and validate_cli_args() is called after parsing to check bounds.
  - Bug 4: Brittle sys.path.insert removed. The new package structure uses
    relative imports (`from .environment import get_environment`) instead of
    manipulating sys.path at runtime to find env_pipeline.
  - Bug 5: `query` command ignored --ticks. The local `ticks = 100` default
    was declared but `--ticks` was never in the query command's arg loop.
    Fixed by adding the `--ticks` branch to the query arg loop.
"""

import json
import sys

import numpy as np

from .algorithms import RandomSearch, Standard_MAP_Elites
from .ca_engine import (
    BIOME_RULE,
    CARule,
    _DENSITY_MAX,
    _DENSITY_MIN,
    _SETTLEMENT_RADIUS_KM,
    compute_density,
    initialize_random,
    step_ca,
)
from .exporters import GodotExporter
from .fitness import classify_topology, has_path
from .validators import validate_cli_args, validate_rule_string


def _parse_int(arg_name: str, raw: str) -> int:
    """Parse a CLI integer arg with a descriptive error on failure."""
    try:
        return int(raw)
    except ValueError:
        print(f"[error] {arg_name} must be an integer, got {raw!r}", file=sys.stderr)
        sys.exit(1)


def _parse_float(arg_name: str, raw: str) -> float:
    """Parse a CLI float arg with a descriptive error on failure."""
    try:
        return float(raw)
    except ValueError:
        print(f"[error] {arg_name} must be a number, got {raw!r}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point for Fung-AI v2.0."""
    if len(sys.argv) < 2:
        print("Fung-AI v2.0 - Game-Design-Aware QD Cave Generator (MAP-Elites)")
        print()
        print("Usage:")
        print("  python -m fung_ai_v2.cli generate --rule B3/S23 --width 100 --height 100 --ticks 50")
        print("  python -m fung_ai_v2.cli generate --lat 10.46 --lon -84.70 --multi-biome --width 99 --height 99")
        print("  python -m fung_ai_v2.cli benchmark --algorithm map_elites --evals 10000")
        print("  python -m fung_ai_v2.cli compare --evals 10000")
        print("  python -m fung_ai_v2.cli export --input cave.json --output godot_scene.json")
        print("  python -m fung_ai_v2.cli query --style branching --algorithm map_elites --evals 10000")
        print()
        print("Algorithms: map_elites, random")
        print("Styles: linear, branching, open")
        return

    command = sys.argv[1]

    if command == "generate":
        rule_str = "B3/S23"
        width, height = 100, 100
        ticks = 50
        seed = 42
        lat = None
        lon = None
        multi_biome = "--multi-biome" in sys.argv

        for i, arg in enumerate(sys.argv):
            if arg == "--rule" and i + 1 < len(sys.argv):
                rule_str = sys.argv[i + 1]
                if not validate_rule_string(rule_str):
                    print(f"[error] --rule must be in B/S notation (e.g. B3/S23), got {rule_str!r}",
                          file=sys.stderr)
                    sys.exit(1)
            elif arg == "--width" and i + 1 < len(sys.argv):
                width = _parse_int("--width", sys.argv[i + 1])
            elif arg == "--height" and i + 1 < len(sys.argv):
                height = _parse_int("--height", sys.argv[i + 1])
            elif arg == "--ticks" and i + 1 < len(sys.argv):
                ticks = _parse_int("--ticks", sys.argv[i + 1])
            elif arg == "--seed" and i + 1 < len(sys.argv):
                seed = _parse_int("--seed", sys.argv[i + 1])
            elif arg == "--lat" and i + 1 < len(sys.argv):
                lat = _parse_float("--lat", sys.argv[i + 1])
            elif arg == "--lon" and i + 1 < len(sys.argv):
                lon = _parse_float("--lon", sys.argv[i + 1])

        # Bug 3 fix: validate bounds after parsing all args.
        try:
            validate_cli_args(width, height, ticks, seed, lat, lon)
        except ValueError as exc:
            print(f"[error] {exc}", file=sys.stderr)
            sys.exit(1)

        if multi_biome and (lat is None or lon is None):
            print("[error] --multi-biome requires --lat and --lon", file=sys.stderr)
            sys.exit(1)

        if multi_biome:
            # Bug 4 fix: use package-relative import instead of sys.path.insert.
            from .environment import get_environment

            tile_w, tile_h = width // 3, height // 3
            actual_width, actual_height = tile_w * 3, tile_h * 3
            if (actual_width, actual_height) != (width, height):
                print(f"[env] --width/--height not divisible by 3, rounded down to "
                      f"{actual_width}x{actual_height}", file=sys.stderr)

            composite = np.zeros((actual_height, actual_width), dtype=np.float32)
            tiles_meta = []
            for row in range(3):
                for col in range(3):
                    sub_lat = lat + (1 - row) * 0.5
                    sub_lon = lon + (col - 1) * 0.5
                    sub_env = get_environment(sub_lat, sub_lon)
                    d = compute_density(sub_env)
                    tile_rule_str = BIOME_RULE.get(d["classification"], "B3/S23")
                    tile_rule = CARule.from_string(tile_rule_str)
                    tile_seed = seed + row * 3 + col

                    nearest_str = (f"{d['nearest_settlement_km']}km"
                                   if d['nearest_settlement_km'] is not None else "none")
                    print(f"[env] tile ({row},{col}) @ ({sub_lat:.4f},{sub_lon:.4f}): "
                          f"biome={d['classification']} rule={tile_rule_str} "
                          f"base_density={d['base_density']} settlement_adj=-{d['settlement_adj']} "
                          f"(nearest={nearest_str}) wind_adj=-{d['wind_adj']} "
                          f"({d['wind_kmh']}km/h) -> final_density={d['final_density']}",
                          file=sys.stderr)

                    tile_grid = initialize_random((tile_h, tile_w), tile_seed,
                                                 density=d["final_density"])
                    for t in range(ticks):
                        tile_grid = step_ca(tile_grid, tile_rule)

                    composite[row * tile_h:(row + 1) * tile_h,
                               col * tile_w:(col + 1) * tile_w] = tile_grid
                    tiles_meta.append({
                        "row": row,
                        "col": col,
                        "lat": sub_lat,
                        "lon": sub_lon,
                        "biome": d["classification"],
                        "rule": tile_rule_str,
                        "density_used": d["final_density"],
                        "base_density": d["base_density"],
                        "settlement_adj": d["settlement_adj"],
                        "wind_adj": d["wind_adj"],
                    })

            result = {
                "rule": "multi-biome",
                "grid": composite.tolist(),
                "width": actual_width,
                "height": actual_height,
                "ticks": ticks,
                "coverage": float(np.mean(composite)),
                "playable": bool(has_path(composite) > 0.5),
                "multi_biome": True,
                "tiles": tiles_meta,
            }
            print(json.dumps(result))
            return

        rule = CARule.from_string(rule_str)

        density = 0.45
        env = None
        if lat is not None and lon is not None:
            # Bug 4 fix: use package-relative import instead of sys.path.insert.
            from .environment import get_environment

            env = get_environment(lat, lon)
            d = compute_density(env)
            density = d["final_density"]

            print(f"[env] fetched real environment snapshot for ({lat}, {lon}):",
                  file=sys.stderr)
            print(f"[env]   biome={d['classification']} "
                  f"(annual_temp_c={env['biome']['annual_temp_c']}, "
                  f"annual_precip_mm={env['biome']['annual_precip_mm']}) "
                  f"-> base_density={d['base_density']}",
                  file=sys.stderr)
            nearest_str = (f"{d['nearest_settlement_km']}km"
                           if d['nearest_settlement_km'] is not None else "none")
            print(f"[env]   settlement_adj=-{d['settlement_adj']} "
                  f"(nearest={nearest_str}, radius={_SETTLEMENT_RADIUS_KM}km) "
                  f"wind_adj=-{d['wind_adj']} (wind_speed_kmh={d['wind_kmh']}) "
                  f"-> final_density={density} (clamped to [{_DENSITY_MIN},{_DENSITY_MAX}])",
                  file=sys.stderr)
            print(f"[env]   elevation_m={env['elevation_m']}", file=sys.stderr)
            print(f"[env]   settlements nearby: {[s['name'] for s in env['settlements']]}",
                  file=sys.stderr)

        grid = initialize_random((height, width), seed, density=density)

        for t in range(ticks):
            grid = step_ca(grid, rule)

        result = {
            "rule": str(rule),
            "grid": grid.tolist(),
            "width": width,
            "height": height,
            "ticks": ticks,
            "coverage": float(np.mean(grid)),
            "playable": bool(has_path(grid) > 0.5),
            "density_used": density,
        }
        if env is not None:
            result["environment"] = env
        print(json.dumps(result))

    elif command == "benchmark":
        evals = 10000
        algo = "map_elites"

        for i, arg in enumerate(sys.argv):
            if arg == "--evals" and i + 1 < len(sys.argv):
                evals = _parse_int("--evals", sys.argv[i + 1])
            elif arg == "--algorithm" and i + 1 < len(sys.argv):
                algo = sys.argv[i + 1]

        if algo == "random":
            alg = RandomSearch()
        else:
            alg = Standard_MAP_Elites()

        archive = alg.run(max_evals=evals, verbose=True)

        stats = archive.get_statistics()
        elites = archive.get_all_elites()
        playable = sum(1 for _, f, _ in elites if f > 0.6)
        results = {
            "coverage": stats["coverage"],
            "qd_score": stats["qd_score"],
            "max_fitness": stats["max_fitness"],
            "success_at_10k": playable / evals,
        }

        print(json.dumps(results, indent=2))

    elif command == "compare":
        evals = 10000

        for i, arg in enumerate(sys.argv):
            if arg == "--evals" and i + 1 < len(sys.argv):
                evals = _parse_int("--evals", sys.argv[i + 1])

        print("=" * 60)
        print("ALGORITHM COMPARISON")
        print("=" * 60)

        algorithms = {
            "Random Search": RandomSearch(),
            "MAP-Elites": Standard_MAP_Elites(),
        }

        comparison = {}
        for name, alg in algorithms.items():
            print(f"\nRunning {name}...")
            archive = alg.run(max_evals=evals, verbose=False)

            stats = archive.get_statistics()
            alg_elites = archive.get_all_elites()
            playable = sum(1 for _, f, _ in alg_elites if f > 0.6)
            res = {
                "coverage": stats["coverage"],
                "qd_score": stats["qd_score"],
                "max_fitness": stats["max_fitness"],
                "success_at_10k": playable / evals,
            }

            comparison[name] = res
            print(f"  Coverage: {res['coverage']:.1%}")
            print(f"  QD-Score: {res['qd_score']:.1f}")
            print(f"  Max Fitness: {res['max_fitness']:.3f}")
            print(f"  Success@10k: {res.get('success_at_10k', 0):.3f}")

        print("\n" + "=" * 60)
        print("COMPARISON TABLE")
        print("=" * 60)
        print(f"{'Algorithm':<20} {'Coverage':<12} {'QD-Score':<12} {'Max Fit':<12} {'Success@10k':<12}")
        print("-" * 60)
        for name, res in comparison.items():
            print(f"{name:<20} {res['coverage']:<12.1%} {res['qd_score']:<12.1f} "
                  f"{res['max_fitness']:<12.3f} {res.get('success_at_10k', 0):<12.3f}")

    elif command == "export":
        input_path = None
        output_path = "godot_scene.json"

        for i, arg in enumerate(sys.argv):
            if arg == "--input" and i + 1 < len(sys.argv):
                input_path = sys.argv[i + 1]
            elif arg == "--output" and i + 1 < len(sys.argv):
                output_path = sys.argv[i + 1]

        if not input_path:
            print("[error] --input required", file=sys.stderr)
            sys.exit(1)

        with open(input_path, 'r') as f:
            data = json.load(f)

        grid = np.array(data["grid"])
        rule = CARule.from_string(data["rule"])

        exporter = GodotExporter()
        scene = exporter.export_to_godot(grid, rule, data["ticks"], output_path)

        print(f"Exported to {output_path}")
        print(f"  Grid size: {grid.shape}")
        print(f"  Playable: {scene['metadata']['playable']}")
        print(f"  Player spawn: {scene['player_spawn']}")

    elif command == "query":
        style = "branching"
        evals = 10000
        algo = "map_elites"
        grid_size = (20, 20)
        # Bug 5 fix: initialize ticks here so --ticks can override it.
        ticks = 100

        for i, arg in enumerate(sys.argv):
            if arg == "--style" and i + 1 < len(sys.argv):
                style = sys.argv[i + 1]
            elif arg == "--evals" and i + 1 < len(sys.argv):
                evals = _parse_int("--evals", sys.argv[i + 1])
            elif arg == "--algorithm" and i + 1 < len(sys.argv):
                algo = sys.argv[i + 1]
            # Bug 5 fix: --ticks was declared but never parsed in the query
            # command's arg loop. Added the missing branch here.
            elif arg == "--ticks" and i + 1 < len(sys.argv):
                ticks = _parse_int("--ticks", sys.argv[i + 1])

        if style not in ("linear", "branching", "open"):
            print(f"[error] --style must be one of linear, branching, open (got {style!r})",
                  file=sys.stderr)
            sys.exit(1)

        if algo == "random":
            alg = RandomSearch()
        else:
            alg = Standard_MAP_Elites()

        archive = alg.run(grid_size=grid_size, ticks=ticks, max_evals=evals, verbose=False)
        all_elites = archive.get_all_elites()

        matches = [(sol, fitness, desc) for sol, fitness, desc in all_elites
                   if classify_topology(float(desc[1])) == style]

        if not matches:
            print(json.dumps({"style": style, "found": False,
                              "message": "No archive cell matches this style."}))
            return

        best_sol, best_fitness, best_desc = max(matches, key=lambda m: m[1])
        rule = CARule.from_genotype(best_sol)
        grid = initialize_random(grid_size, seed=42)
        for t in range(ticks):
            grid = step_ca(grid, rule)

        result = {
            "style": style,
            "found": True,
            "rule": str(rule),
            "fitness": float(best_fitness),
            "descriptors": {
                "coverage": float(best_desc[0]),
                "path_topology_score": float(best_desc[1]),
                "chokepoint_density": float(best_desc[2]),
            },
            "grid": grid.tolist(),
            "playable": bool(has_path(grid) > 0.5),
        }
        print(json.dumps(result))

    else:
        print(f"[error] Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
