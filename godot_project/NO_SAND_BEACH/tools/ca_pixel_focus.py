"""CA-Dissolved Pixel Focus: the NO SAND BEACH render technique from RENDER_STYLE.md.

Pipeline: source image -> grayscale -> threshold (chunky pixel-art base) ->
cellular-automata edge dissolution, with dissolution strength scaling by
distance from a focus point (faces stay crisp, everything else softens into
organic shapes) -> upscaled black-and-white output.

Reuses fung_ai_v2.ca_engine.step_ca (the same Moore-neighborhood CA already
used for cave-wall smoothing) as the dissolution operator, run once per
sequence step and cached, then composited per-cell by target iteration count
-- a single global CA step can't vary spatially on its own, so this runs the
CA forward to its maximum needed depth and picks, cell by cell, the snapshot
matching that cell's local dissolution target.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from fung_ai_v2.ca_engine import CARule, step_ca

# Smooth, convergent rule -- same family used for cave-wall generation.
# Produces organic blob-like dissolution rather than chaotic noise.
SMOOTH_DISSOLVE_RULE = CARule.from_string("B3/S2345678")

# Chaotic, non-convergent rule -- for Earl's glitch thread-mask (RENDER_STYLE.md,
# "Earl's Glitch State" section). Classic Life is a good chaotic baseline.
CHOPPY_GLITCH_RULE = CARule.from_string("B3/S23")


def pixelate(image: Image.Image, block_size: int, threshold: int = 128) -> np.ndarray:
    """Grayscale + downsample + threshold into a binary grid (1=ink, 0=paper).

    This is the "chunky pixel art base" step -- deliberately low-fidelity.
    """
    gray = image.convert("L")
    small_w = max(1, gray.width // block_size)
    small_h = max(1, gray.height // block_size)
    small = gray.resize((small_w, small_h), Image.BILINEAR)
    arr = np.array(small, dtype=np.uint8)
    return (arr < threshold).astype(np.float32)  # dark pixels -> 1 (ink)


def build_focus_iteration_map(
    shape: tuple[int, int],
    focus_center: tuple[float, float],
    focus_radius: float,
    max_iterations: int,
) -> np.ndarray:
    """Per-cell target CA iteration count: 0 at the focus point, rising with distance.

    focus_center and focus_radius are in the *pixelated grid's* coordinate
    space (row, col), not the source image's pixel space.
    """
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((yy - focus_center[0]) ** 2 + (xx - focus_center[1]) ** 2)
    normalized = np.clip((dist - focus_radius) / max(focus_radius, 1e-6), 0.0, 1.0)
    return np.round(normalized * max_iterations).astype(np.int32)


def run_ca_snapshots(grid: np.ndarray, rule: CARule, max_iterations: int) -> list[np.ndarray]:
    """Run the CA forward, keeping every intermediate grid (snapshots[0] = input)."""
    snapshots = [grid.copy()]
    current = grid
    for _ in range(max_iterations):
        current = step_ca(current, rule)
        snapshots.append(current.copy())
    return snapshots


def composite_by_focus(snapshots: list[np.ndarray], iteration_map: np.ndarray) -> np.ndarray:
    """For each cell, pull its value from the snapshot matching its target iteration count."""
    stacked = np.stack(snapshots, axis=0)  # (max_iter+1, H, W)
    return np.take_along_axis(stacked, iteration_map[np.newaxis, :, :], axis=0)[0]


def upscale(grid: np.ndarray, factor: int) -> Image.Image:
    """Nearest-neighbor block upscale, binary grid -> black-and-white PIL Image."""
    img_arr = ((1.0 - grid) * 255).astype(np.uint8)  # ink(1)->black(0), paper(0)->white(255)
    img = Image.fromarray(img_arr, mode="L")
    return img.resize((img.width * factor, img.height * factor), Image.NEAREST)


def ca_dissolved_pixel_focus(
    source_path: str,
    output_path: str,
    *,
    block_size: int = 12,
    focus_center_frac: tuple[float, float] = (0.35, 0.5),
    focus_radius_frac: float = 0.12,
    max_iterations: int = 6,
    upscale_factor: int = 8,
    rule: CARule = SMOOTH_DISSOLVE_RULE,
    threshold: int = 128,
) -> None:
    """End-to-end: source photo/art -> CA-dissolved pixel-focus black-and-white output.

    focus_center_frac / focus_radius_frac are fractions of the pixelated grid's
    (height, width) -- e.g. (0.35, 0.5) targets a point 35% down, 50% across,
    which is roughly where a face sits in a head-and-shoulders portrait.
    """
    source = Image.open(source_path)
    grid = pixelate(source, block_size, threshold)
    iteration_map = build_focus_iteration_map(
        grid.shape,
        focus_center=(grid.shape[0] * focus_center_frac[0], grid.shape[1] * focus_center_frac[1]),
        focus_radius=grid.shape[0] * focus_radius_frac,
        max_iterations=max_iterations,
    )
    snapshots = run_ca_snapshots(grid, rule, max_iterations)
    composited = composite_by_focus(snapshots, iteration_map)
    result = upscale(composited, upscale_factor)
    result.save(output_path)
    print(f"wrote {output_path} ({result.width}x{result.height}, "
          f"base grid {grid.shape[1]}x{grid.shape[0]}, {max_iterations} max CA iterations)")


def make_synthetic_test_image(path: str, size: int = 256) -> None:
    """Generate a simple synthetic face-like test pattern -- no real person involved.

    Exists purely to prove the pipeline runs end-to-end without needing a real
    reference photo as input.
    """
    img = Image.new("L", (size, size), color=255)
    arr = np.array(img)
    yy, xx = np.mgrid[0:size, 0:size]
    # Head oval.
    head = ((xx - size * 0.5) ** 2 / (size * 0.3) ** 2 + (yy - size * 0.45) ** 2 / (size * 0.38) ** 2) < 1
    arr[head] = 60
    # Eyes.
    for ex in (0.38, 0.62):
        eye = ((xx - size * ex) ** 2 + (yy - size * 0.4) ** 2) < (size * 0.045) ** 2
        arr[eye] = 250
    # Mouth.
    mouth = (np.abs(xx - size * 0.5) < size * 0.12) & (np.abs(yy - size * 0.6) < size * 0.02)
    arr[mouth] = 20
    # Shoulders (rough triangle at the bottom, gives the focus-falloff something to dissolve).
    shoulders = (yy > size * 0.75) & (np.abs(xx - size * 0.5) < (yy - size * 0.7))
    arr[shoulders] = 90
    Image.fromarray(arr, mode="L").save(path)
    print(f"wrote synthetic test image: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    synth = sub.add_parser("make-test-image", help="Generate a synthetic test image (no real person)")
    synth.add_argument("output", help="Output PNG path")
    synth.add_argument("--size", type=int, default=256)

    run = sub.add_parser("run", help="Run the CA-dissolved pixel focus pipeline")
    run.add_argument("source", help="Source image path")
    run.add_argument("output", help="Output PNG path")
    run.add_argument("--block-size", type=int, default=12)
    run.add_argument("--max-iterations", type=int, default=6)
    run.add_argument("--upscale-factor", type=int, default=8)
    run.add_argument("--rule", choices=["smooth", "choppy"], default="smooth")
    run.add_argument("--threshold", type=int, default=128)

    args = parser.parse_args()

    if args.command == "make-test-image":
        make_synthetic_test_image(args.output, size=args.size)
    elif args.command == "run":
        rule = SMOOTH_DISSOLVE_RULE if args.rule == "smooth" else CHOPPY_GLITCH_RULE
        ca_dissolved_pixel_focus(
            args.source,
            args.output,
            block_size=args.block_size,
            max_iterations=args.max_iterations,
            upscale_factor=args.upscale_factor,
            rule=rule,
            threshold=args.threshold,
        )


if __name__ == "__main__":
    main()
