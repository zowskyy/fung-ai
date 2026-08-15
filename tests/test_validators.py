"""
W7: 8 tests for the validators module (fung_ai_v2/validators.py).
If the module is not yet created by W1-W3, all tests are skipped at module level.
"""

import numpy as np
import pytest

try:
    from fung_ai_v2.validators import validate_rule_string, validate_grid, validate_cli_args, sanitize_path
except ImportError:
    pytest.skip("validators module not ready (fung_ai_v2/validators.py not yet created)", allow_module_level=True)


# ---------------------------------------------------------------------------
# validate_rule_string
# ---------------------------------------------------------------------------

def test_validate_rule_string_valid_b3s23():
    """Well-formed 'B3/S23' is a valid rule string."""
    assert validate_rule_string("B3/S23") is True


def test_validate_rule_string_valid_b36s23():
    """'B36/S23' is a valid rule string."""
    assert validate_rule_string("B36/S23") is True


def test_validate_rule_string_invalid_eval():
    """String containing 'eval()' must be rejected (injection guard)."""
    assert validate_rule_string("eval()") is False


def test_validate_rule_string_malformed():
    """Completely malformed string must be rejected."""
    assert validate_rule_string("bad_rule") is False


# ---------------------------------------------------------------------------
# validate_grid
# ---------------------------------------------------------------------------

def test_validate_grid_valid():
    """A 20x20 float32 array is a valid grid."""
    g = np.zeros((20, 20), dtype=np.float32)
    assert validate_grid(g) is True


def test_validate_grid_1d():
    """A 1D array is not a valid grid — must be 2D."""
    g = np.zeros(400, dtype=np.float32)
    assert validate_grid(g) is False


# ---------------------------------------------------------------------------
# validate_cli_args
# ---------------------------------------------------------------------------

def test_validate_cli_args_valid():
    """Valid CLI args (width, height, ticks, seed, lat, lon) return True."""
    assert validate_cli_args(50, 50, 12, 42, None, None) is True


def test_validate_cli_args_width_too_large():
    """Width of 999 (unreasonably large) should raise ValueError."""
    with pytest.raises(ValueError):
        validate_cli_args(999, 50, 12, 42, None, None)


# ---------------------------------------------------------------------------
# Additional edge case tests for uncovered lines (100% coverage push)
# ---------------------------------------------------------------------------

def test_validate_grid_not_ndarray():
    """A Python list instead of ndarray should be rejected (line 17)."""
    assert validate_grid([1, 2, 3]) is False


def test_validate_grid_too_small():
    """A 4x4 grid (below 5x5 minimum) should be rejected (line 21)."""
    g = np.zeros((4, 4), dtype=np.float32)
    assert validate_grid(g) is False


def test_validate_cli_args_height_too_large():
    """Height of 999 (unreasonably large) should raise ValueError (line 41)."""
    with pytest.raises(ValueError, match="height"):
        validate_cli_args(50, 999, 12, 42, None, None)


def test_validate_cli_args_ticks_zero():
    """Ticks of 0 should raise ValueError (line 41)."""
    with pytest.raises(ValueError, match="ticks"):
        validate_cli_args(50, 50, 0, 42, None, None)


def test_validate_cli_args_ticks_too_high():
    """Ticks of 201 should raise ValueError (line 41)."""
    with pytest.raises(ValueError, match="ticks"):
        validate_cli_args(50, 50, 201, 42, None, None)


def test_validate_cli_args_seed_too_high():
    """Seed of 2^32 should raise ValueError (line 43)."""
    with pytest.raises(ValueError, match="seed"):
        validate_cli_args(50, 50, 100, 2**32, None, None)


def test_validate_cli_args_latitude_too_low():
    """Latitude of -91 should raise ValueError (line 47)."""
    with pytest.raises(ValueError, match="lat"):
        validate_cli_args(50, 50, 100, 42, -91.0, 0.0)


def test_validate_cli_args_latitude_too_high():
    """Latitude of 91 should raise ValueError (line 47)."""
    with pytest.raises(ValueError, match="lat"):
        validate_cli_args(50, 50, 100, 42, 91.0, 0.0)


def test_validate_cli_args_longitude_too_low():
    """Longitude of -181 should raise ValueError (line 49)."""
    with pytest.raises(ValueError, match="lon"):
        validate_cli_args(50, 50, 100, 42, 0.0, -181.0)


def test_validate_cli_args_longitude_too_high():
    """Longitude of 181 should raise ValueError (line 49)."""
    with pytest.raises(ValueError, match="lon"):
        validate_cli_args(50, 50, 100, 42, 0.0, 181.0)


def test_sanitize_path_absolute():
    """Absolute paths pass through (may be used externally, so kept as-is)."""
    from pathlib import Path
    # Build a platform-correct absolute path (Windows requires a drive letter).
    abs_path = Path(Path.cwd().anchor, "some_absolute_dir", "file.txt")
    result = sanitize_path(str(abs_path), Path("/home/user"))
    assert result == abs_path


def test_sanitize_path_relative_safe():
    """Relative paths are joined with base_dir."""
    from pathlib import Path
    result = sanitize_path("data/config.json", Path("/home/user"))
    assert "data" in str(result) and "config.json" in str(result)


def test_sanitize_path_traversal_attack():
    """Directory traversal attempts (../) are rejected (line 63-66)."""
    from pathlib import Path
    with pytest.raises(ValueError):
        sanitize_path("../../../etc/passwd", Path("/home/user"))
