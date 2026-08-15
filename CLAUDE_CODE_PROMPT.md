# Claude Code Prompt: CA Dungeon Generator – SLICE_001

**Copy this entire prompt into Claude Code and run it.**

---

## Context

You are building **CA Dungeon Generator**, a cellular automaton-based procedural cave/dungeon tilemap generator. This is **SLICE_001: Implement CA cave carving rules + validators**.

**Your operating mode:** Shipping-focused. Every artifact must be:
1. **Testable in isolation** (unit tests included)
2. **Security-gated** (no eval/exec, no unvalidated input)
3. **Validated before merge** (tests pass, edge cases covered)
4. **Production-ready** on day one (not "we'll fix it next sprint")

---

## What You're Building (SLICE_001)

**Acceptance Criteria:**
- Generate 50 distinct cave systems (using CA rules) without crashes
- Each cave must be valid: grid is M×N, cells are 0 (wall) or 1 (floor)
- Rule notation: "B23/S3" (Conway birth/survival rules) or custom ruleset
- Output: JSON tilemap format (floor/wall/void)
- Execution: < 100ms per cave (50×50 grid)

**Deliverables:**
1. `ca_engine.py` – Core CA rule engine + grid iteration
2. `validators.py` – Input validation (rules, grid size, seed)
3. `tilemap.py` – JSON output formatting
4. `test_ca_engine.py` – Unit tests (pytest)
5. `test_validators.py` – Input validation tests
6. `README.md` – Usage docs + examples

---

## Task Breakdown

### **Step 1: Core CA Engine** (`ca_engine.py`)

```python
# ca_engine.py

"""
Cellular automaton engine for cave generation.
- Rule notation: "B23/S3" (birth rules 2-3, survival rule 3)
- Custom rulesets supported
- Fixed timestep iteration (50–100 steps typical)
"""

from dataclasses import dataclass
from typing import List, Tuple, Set
import random


@dataclass
class CARules:
    """Cellular automaton rules (birth/survival counts)."""
    birth: Set[int]  # Neighbor counts that create a cell
    survival: Set[int]  # Neighbor counts that keep a cell alive


def parse_rule_notation(notation: str) -> CARules:
    """
    Parse rule notation: "B23/S3" → birth {2,3}, survival {3}
    
    Also accepts:
    - "23/3" (implicit B/S)
    - "2,3/3" (commas)
    - Validation: all numbers 0-8 (valid neighbor counts)
    
    Raises ValueError on invalid input.
    """
    # Your implementation here


def grid_init(width: int, height: int, seed: int | None = None, density: float = 0.45) -> List[List[int]]:
    """
    Initialize random grid: 1 = alive, 0 = dead.
    density: fraction of cells that start alive (0.0-1.0).
    Typical: 0.45 for cave generation.
    """
    # Your implementation here


def count_neighbors(grid: List[List[int]], x: int, y: int) -> int:
    """Count alive neighbors (Moore neighborhood, 8 adjacent cells)."""
    # Your implementation here


def step(grid: List[List[int]], rules: CARules) -> List[List[int]]:
    """
    Apply CA rules for one timestep.
    Returns new grid (non-mutating).
    """
    # Your implementation here


def evolve(grid: List[List[int]], rules: CARules, steps: int) -> List[List[int]]:
    """
    Run CA for N steps. Returns final grid.
    """
    # Your implementation here


def generate_cave(width: int, height: int, rule_notation: str, iterations: int = 50, seed: int | None = None) -> List[List[int]]:
    """
    High-level API: generate a cave and return grid.
    
    Args:
        width, height: grid dimensions (must be > 0)
        rule_notation: "B23/S3" or similar
        iterations: CA steps (50 typical, 10-200 valid range)
        seed: random seed (None = random)
    
    Returns:
        2D list of 0s (wall) and 1s (floor)
    
    Raises:
        ValueError on invalid inputs
    """
    # Your implementation here
```

**Tests you must write:**
```python
# test_ca_engine.py

import pytest
from ca_engine import parse_rule_notation, CARules, grid_init, count_neighbors, step, generate_cave


def test_parse_rule_notation():
    """Parse "B23/S3" correctly."""
    rules = parse_rule_notation("B23/S3")
    assert rules.birth == {2, 3}
    assert rules.survival == {3}


def test_parse_rule_notation_short_form():
    """Parse "23/3" (implicit B/S)."""
    rules = parse_rule_notation("23/3")
    assert rules.birth == {2, 3}
    assert rules.survival == {3}


def test_parse_rule_notation_invalid_raises():
    """Invalid rules raise ValueError."""
    with pytest.raises(ValueError):
        parse_rule_notation("B9/S3")  # 9 is out of range
    
    with pytest.raises(ValueError):
        parse_rule_notation("invalid")


def test_grid_init():
    """Initialize grid with correct dimensions."""
    grid = grid_init(10, 10, seed=42)
    assert len(grid) == 10
    assert len(grid[0]) == 10
    assert all(cell in {0, 1} for row in grid for cell in row)


def test_count_neighbors():
    """Count neighbors correctly (Moore neighborhood)."""
    grid = [
        [1, 1, 0],
        [1, 0, 0],
        [0, 0, 0],
    ]
    # Center cell (1,1) has 3 neighbors
    assert count_neighbors(grid, 1, 1) == 3


def test_step_conway():
    """Apply Conway's Life rules (B3/S23)."""
    # Blinker pattern: should oscillate
    grid = [
        [0, 1, 0],
        [0, 1, 0],
        [0, 1, 0],
    ]
    rules = CARules(birth={3}, survival={2, 3})
    grid2 = step(grid, rules)
    
    # After 1 step, should rotate 90°
    expected = [
        [0, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ]
    assert grid2 == expected


def test_generate_cave_dimensions():
    """Generated cave has correct dimensions."""
    cave = generate_cave(50, 50, "B23/S3", iterations=50)
    assert len(cave) == 50
    assert len(cave[0]) == 50


def test_generate_cave_no_crashes():
    """Generate 50 caves without crashes."""
    for i in range(50):
        cave = generate_cave(50, 50, "B23/S3", iterations=50, seed=i)
        assert cave  # Not empty


def test_generate_cave_performance():
    """Generate 50x50 cave in < 100ms."""
    import time
    start = time.time()
    cave = generate_cave(50, 50, "B23/S3", iterations=50)
    elapsed = (time.time() - start) * 1000
    assert elapsed < 100, f"Cave generation took {elapsed}ms (target: <100ms)"
```

---

### **Step 2: Input Validators** (`validators.py`)

Adapt from **repurpose-engine/repurpose.py** (copy the cleaning/validation pattern):

```python
# validators.py

"""
Input validators for CA engine.
Adapted from repurpose-engine/repurpose.py validation patterns.
"""

import re


RULE_PATTERN = re.compile(r"^B[0-8]*/S[0-8]*$", re.IGNORECASE)


def validate_rule_notation(rule_str: str) -> bool:
    """
    Validate rule notation format.
    - Must match "B23/S3" or "23/3" format
    - All numbers 0-8 only
    - Raises ValueError on invalid input
    """
    if not isinstance(rule_str, str):
        raise ValueError(f"Rule must be string, got {type(rule_str)}")
    
    # Your implementation here


def validate_grid_size(width: int, height: int) -> bool:
    """
    Validate grid dimensions.
    - Both must be integers
    - Both must be > 0
    - Both must be <= 1000 (memory/performance limit)
    """
    # Your implementation here


def validate_iterations(iterations: int) -> bool:
    """
    Validate CA iteration count.
    - Must be integer
    - Must be 1-1000
    """
    # Your implementation here


def validate_seed(seed: int | None) -> bool:
    """Validate random seed if provided."""
    if seed is None:
        return True
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be int or None, got {type(seed)}")
    if seed < 0:
        raise ValueError(f"Seed must be >= 0, got {seed}")
    return True


# Tests
import pytest


def test_validate_rule_notation():
    """Accept valid rules, reject invalid."""
    assert validate_rule_notation("B23/S3")
    assert validate_rule_notation("23/3")
    
    with pytest.raises(ValueError):
        validate_rule_notation("B9/S3")  # 9 is invalid
    
    with pytest.raises(ValueError):
        validate_rule_notation(123)  # Not a string


def test_validate_grid_size():
    """Accept valid sizes, reject invalid."""
    assert validate_grid_size(50, 50)
    assert validate_grid_size(1, 1)
    assert validate_grid_size(1000, 1000)
    
    with pytest.raises(ValueError):
        validate_grid_size(0, 50)  # Width must be > 0
    
    with pytest.raises(ValueError):
        validate_grid_size(1001, 50)  # Too large
```

---

### **Step 3: Tilemap Output** (`tilemap.py`)

```python
# tilemap.py

"""
JSON tilemap output formatting.
Converts 2D grid (0s and 1s) to JSON with metadata.
"""

import json
from dataclasses import dataclass, asdict
from typing import List


@dataclass
class TilemapMetadata:
    """Metadata for generated tilemap."""
    width: int
    height: int
    rule: str
    iterations: int
    seed: int | None
    cell_count: int  # Total non-zero cells


def grid_to_tilemap_json(grid: List[List[int]], rule: str, iterations: int, seed: int | None = None) -> str:
    """
    Convert grid to JSON tilemap.
    
    Output format:
    {
        "metadata": {
            "width": 50,
            "height": 50,
            "rule": "B23/S3",
            "iterations": 50,
            "seed": 12345,
            "cell_count": 1234
        },
        "grid": [[0, 1, 0, ...], ...]
    }
    """
    width = len(grid[0]) if grid else 0
    height = len(grid)
    cell_count = sum(sum(row) for row in grid)
    
    # Your implementation here


def tilemap_json_to_grid(json_str: str) -> List[List[int]]:
    """Deserialize JSON back to grid."""
    # Your implementation here


# Test
def test_grid_to_tilemap_json():
    """Convert grid to valid JSON."""
    grid = [[1, 0], [0, 1]]
    json_str = grid_to_tilemap_json(grid, "B23/S3", 50, seed=42)
    
    data = json.loads(json_str)
    assert data["metadata"]["width"] == 2
    assert data["metadata"]["height"] == 2
    assert data["metadata"]["cell_count"] == 2
    assert data["grid"] == grid
```

---

### **Step 4: Security Gate** (Pre-commit check)

Copy from **apex-android/cursor_gate.py**:

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: cursor_gate
        name: Cursor Security Gate
        entry: python3 cursor_gate.py --file
        language: system
        types: [python]
        stages: [commit]
```

**Things to check:**
- [ ] No `eval()`, `exec()`, `os.system()`
- [ ] No `pickle.load()` or `yaml.load()`
- [ ] No unvalidated input (grid size, rule notation must be validated before use)
- [ ] No secrets (API keys, passwords in code)
- [ ] No sensitive data in logs

---

## Instructions for Claude Code

1. **Start with `ca_engine.py`.**
   - Implement `parse_rule_notation()` first (simplest, testable in isolation)
   - Then `grid_init()`, `count_neighbors()`, `step()`, `evolve()`
   - Run tests after each function

2. **Then `validators.py`.**
   - Reuse patterns from repurpose-engine/repurpose.py
   - Keep validation simple: type checks + range checks

3. **Then `tilemap.py`.**
   - JSON serialization (no custom code, use stdlib `json` module)

4. **Run all tests.**
   ```bash
   python3 -m pytest test_ca_engine.py test_validators.py -v
   ```

5. **Security gate (manual check for now):**
   ```bash
   grep -r "eval\|exec\|pickle\|yaml.load" *.py  # Should find nothing
   ```

6. **Output: Commit to GitHub with message:**
   ```
   git commit -m "slice-001: CA cave generation engine (parser + validators + tests)"
   ```

---

## Success Criteria (SLICE_001 Complete)

- [ ] All 10+ unit tests pass (0 failures, 0 skips)
- [ ] `generate_cave()` creates 50 distinct caves without crashes
- [ ] Each cave: valid JSON, correct grid dimensions, < 100ms generation time
- [ ] Security gate: no eval/exec/pickle, no unvalidated input
- [ ] README with usage examples:
  ```python
  from ca_engine import generate_cave
  
  cave = generate_cave(50, 50, "B23/S3", iterations=50, seed=42)
  # Returns: [[0, 1, 0, ...], ...]
  ```

---

## What NOT to Do

❌ Don't over-engineer. This is SLICE_001; keep it simple.  
❌ Don't add UI, no Godot integration yet (SLICE_006).  
❌ Don't support custom tile types (floor/wall/void); just 0/1 for now.  
❌ Don't parallelize grid iteration (single-threaded is fine for 50×50).  
❌ Don't commit if tests fail or security gate finds issues.

---

## Next Steps (After SLICE_001)

- **SLICE_002:** Tilemap JSON → Godot-compatible format
- **SLICE_003:** Python CLI wrapper (argparse)
- **SLICE_004:** Connectivity checker (all floors reachable)
- **SLICE_005:** Difficulty scorer (playability metric)
- **SLICE_006:** Godot plugin (GDScript wrapper)
- **SLICE_007:** Tilemap painter (collision + visual)
- **SLICE_008:** GUTTERUMBLE integration
- **SLICE_009:** GitHub release + docs
- **SLICE_010:** Security audit pass

---

## Estimation

**SLICE_001 should take 2–3 hours:**
- CA engine: 60 min (parse rules, grid init, neighbor count, step, evolve)
- Tests: 45 min (10 tests, edge cases)
- Validators: 30 min (input validation)
- Tilemap: 15 min (JSON serialization)
- Security gate + cleanup: 15 min

**Total: 2.5 hours wall-clock if you stay focused.**

---

## Go Build

Copy this prompt. Open Claude Code. Paste. Run. Ship.

You've got this. 🚀
