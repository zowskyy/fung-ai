"""Input validation for fung_ai_v2 CLI and API."""
import re
from pathlib import Path

import numpy as np


def validate_rule_string(rule_str: str) -> bool:
    """Validate B/S notation: e.g. B3/S23, B36/S23. No eval."""
    pattern = r'^B[0-8]*/S[0-8]*$'
    return bool(re.match(pattern, rule_str))


def validate_grid(grid: np.ndarray) -> bool:
    """Grid must be 2D, numeric, shape > (5,5)."""
    if not isinstance(grid, np.ndarray):
        return False
    if grid.ndim != 2:
        return False
    if grid.shape[0] < 5 or grid.shape[1] < 5:
        return False
    return True


def validate_cli_args(
    width: int,
    height: int,
    ticks: int,
    seed: int,
    lat: float | None,
    lon: float | None,
) -> bool:
    """Validate CLI argument bounds.

    Raises ValueError with a descriptive message on the first invalid arg.
    Returns True if all args are valid.
    """
    if not (10 <= width <= 500):
        raise ValueError(f"width must be 10-500, got {width}")
    if not (10 <= height <= 500):
        raise ValueError(f"height must be 10-500, got {height}")
    if not (1 <= ticks <= 200):
        raise ValueError(f"ticks must be 1-200, got {ticks}")
    if not (0 <= seed <= 2**31 - 1):
        raise ValueError(f"seed must be 0 to 2147483647, got {seed}")
    if lat is not None and not (-90 <= lat <= 90):
        raise ValueError(f"lat must be -90 to 90, got {lat}")
    if lon is not None and not (-180 <= lon <= 180):
        raise ValueError(f"lon must be -180 to 180, got {lon}")
    return True


def sanitize_path(path_str: str, base_dir: Path | None = None) -> Path:
    """Reject path traversal, return safe Path.

    Absolute paths are returned as-is (callers may restrict further).
    Relative paths are resolved against `base_dir` (if given) and checked
    to ensure they do not escape the base directory.
    """
    p = Path(path_str)
    if p.is_absolute():
        # Allow absolute for output paths; callers can restrict further.
        return p
    resolved = (base_dir / p).resolve() if base_dir else p.resolve()
    if base_dir and not str(resolved).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path traversal rejected: {path_str}")
    return resolved
