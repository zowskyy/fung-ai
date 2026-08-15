"""Integration tests for the CA generation pipeline (bridge/generation.py).

These exercise real fung_ai_v2 calls end-to-end (not just schema shapes) so
signature mismatches between bridge/generation.py and fung_ai_v2 are caught.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from bridge.generation import (
    RECIPES,
    CandidateGrid,
    compute_candidate_metrics,
    compute_generation_inputs_hash,
    encode_grid_rle,
    generate_candidate_grid,
    tags_from_metrics,
)


class TestGenerateCandidateGrid:
    """Test real CA generation against fung_ai_v2."""

    def test_generates_valid_candidate(self) -> None:
        """A known seed/recipe/size should produce a connected candidate."""
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)

        assert candidate is not None
        assert isinstance(candidate, CandidateGrid)
        assert candidate.grid.shape == (48, 48)
        assert set(np.unique(candidate.grid).tolist()) <= {0.0, 1.0}

    def test_spawn_and_exit_on_floor(self) -> None:
        """Spawn and exit cells must be walkable (floor, not wall)."""
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)

        assert candidate is not None
        spawn_x, spawn_y = candidate.spawn_cell
        exit_x, exit_y = candidate.exit_cell
        assert candidate.grid[spawn_y, spawn_x] == 0
        assert candidate.grid[exit_y, exit_x] == 0

    def test_spawn_near_top_exit_near_bottom(self) -> None:
        """Spawn should sit on the top edge, exit on the bottom edge."""
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)

        assert candidate is not None
        assert candidate.spawn_cell[1] == 0
        assert candidate.exit_cell[1] == 47

    def test_deterministic_for_same_seed(self) -> None:
        """Same seed + recipe + size must produce an identical grid."""
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate_a = generate_candidate_grid(555, (32, 32), recipe)
        candidate_b = generate_candidate_grid(555, (32, 32), recipe)

        assert candidate_a is not None
        assert candidate_b is not None
        assert np.array_equal(candidate_a.grid, candidate_b.grid)
        assert candidate_a.spawn_cell == candidate_b.spawn_cell
        assert candidate_a.exit_cell == candidate_b.exit_cell

    def test_progress_callback_invoked(self) -> None:
        """Progress callback should fire during generation."""
        recipe = RECIPES["compact_roguelike_rooms"]
        calls: list[tuple[float, str]] = []
        generate_candidate_grid(1000, (32, 32), recipe, lambda p, msg: calls.append((p, msg)))

        assert len(calls) > 0

    @pytest.mark.parametrize("recipe_id", list(RECIPES.keys()))
    def test_all_builtin_recipes_can_generate(self, recipe_id: str) -> None:
        """Every built-in recipe should be able to produce a valid candidate
        for at least one of a handful of seeds (CA generation is stochastic).
        """
        recipe = RECIPES[recipe_id]
        found_valid = False
        for seed in range(5):
            candidate = generate_candidate_grid(seed, (48, 48), recipe)
            if candidate is not None:
                found_valid = True
                break
        assert found_valid, f"Recipe '{recipe_id}' produced no valid candidate in 5 seeds"


class TestComputeCandidateMetrics:
    """Test metrics computation on real generated candidates."""

    def test_metrics_have_expected_keys(self) -> None:
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)
        assert candidate is not None

        metrics = compute_candidate_metrics(candidate, recipe)
        expected_keys = (
            "walkable_ratio",
            "path_length",
            "loop_count",
            "branch_count",
            "open_space_score",
            "score",
        )
        for key in expected_keys:
            assert key in metrics

    def test_walkable_ratio_in_unit_range(self) -> None:
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)
        assert candidate is not None

        metrics = compute_candidate_metrics(candidate, recipe)
        assert 0.0 <= metrics["walkable_ratio"] <= 1.0

    def test_path_length_positive(self) -> None:
        """A valid candidate (spawn connected to exit) must have path_length > 0."""
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)
        assert candidate is not None

        metrics = compute_candidate_metrics(candidate, recipe)
        assert metrics["path_length"] > 0

    def test_score_is_deterministic(self) -> None:
        """Score must not depend on unseeded randomness."""
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)
        assert candidate is not None

        metrics_a = compute_candidate_metrics(candidate, recipe)
        metrics_b = compute_candidate_metrics(candidate, recipe)
        assert metrics_a["score"] == metrics_b["score"]

    def test_tags_from_metrics_returns_list(self) -> None:
        recipe = RECIPES["compact_roguelike_rooms"]
        candidate = generate_candidate_grid(1000, (48, 48), recipe)
        assert candidate is not None

        metrics = compute_candidate_metrics(candidate, recipe)
        tags = tags_from_metrics(metrics)
        assert isinstance(tags, list)
        assert len(tags) <= 4


class TestEncodeGridRle:
    """Test RLE grid encoding round-trips correctly."""

    def test_encoded_cell_count_matches_grid_size(self) -> None:
        grid = np.zeros((10, 10), dtype=np.float32)
        grid[3:6, 3:6] = 1.0
        encoded = encode_grid_rle(grid)

        assert encoded.startswith("rle-v1:")
        parts = encoded.split(":")[1:]
        total_cells = sum(int(parts[i]) for i in range(0, len(parts), 2))
        assert total_cells == 100

    def test_decodes_back_to_original(self) -> None:
        """Manually decode the RLE string and compare to the source grid."""
        rng = np.random.RandomState(7)
        grid = (rng.random((16, 16)) < 0.4).astype(np.float32)
        encoded = encode_grid_rle(grid)

        parts = encoded.split(":")[1:]
        decoded_flat: list[int] = []
        for i in range(0, len(parts), 2):
            count = int(parts[i])
            value = int(parts[i + 1])
            decoded_flat.extend([value] * count)

        decoded = np.array(decoded_flat, dtype=np.float32).reshape(grid.shape)
        assert np.array_equal(decoded, grid)


class TestComputeGenerationInputsHash:
    """Test reproducibility hash is stable and sensitive to inputs."""

    def test_same_inputs_same_hash(self) -> None:
        recipe = RECIPES["compact_roguelike_rooms"]
        hash_a = compute_generation_inputs_hash(recipe, 42, (48, 48))
        hash_b = compute_generation_inputs_hash(recipe, 42, (48, 48))
        assert hash_a == hash_b

    def test_different_seed_different_hash(self) -> None:
        recipe = RECIPES["compact_roguelike_rooms"]
        hash_a = compute_generation_inputs_hash(recipe, 42, (48, 48))
        hash_b = compute_generation_inputs_hash(recipe, 43, (48, 48))
        assert hash_a != hash_b

    def test_hash_has_sha256_prefix(self) -> None:
        recipe = RECIPES["compact_roguelike_rooms"]
        result = compute_generation_inputs_hash(recipe, 42, (48, 48))
        assert result.startswith("sha256:")


class TestBridgeCliEndToEnd:
    """Full subprocess invocation of the bridge CLI, matching how Godot calls it."""

    def test_full_pipeline_writes_expected_files(self, tmp_path: Path) -> None:
        job_dir = tmp_path / "job"
        job_dir.mkdir()
        request_path = job_dir / "request.json"
        result_path = job_dir / "result.json"

        request_path.write_text(
            """{
                "protocol_version": 1,
                "request_id": "test_cli_e2e",
                "generator_version": "0.1.0",
                "recipe_id": "compact_roguelike_rooms",
                "seed": 1000,
                "map_size_tiles": [32, 32],
                "tile_size_px": [16, 16],
                "generation_budget": "fast",
                "environment_mode": "manual_preset",
                "environment_preset": "limestone_cave",
                "overrides": {},
                "candidate_count": 24,
                "job_dir": "%s",
                "result_path": "%s",
                "status_path": "%s",
                "cancel_path": "%s"
            }"""
            % (
                job_dir,
                result_path,
                job_dir / "status.json",
                job_dir / "cancel.request",
            )
        )

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "bridge.fung_bridge",
                "--request",
                str(request_path),
                "--response",
                str(result_path),
            ],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert completed.returncode == 0, completed.stderr

        assert result_path.exists()
        assert (job_dir / "status.json").exists()

        import json

        result = json.loads(result_path.read_text())
        assert result["success"] is True
        assert len(result["candidates"]) > 0

        first_candidate = result["candidates"][0]
        payload_path = job_dir / first_candidate["payload_path"]
        assert payload_path.exists()

        payload = json.loads(payload_path.read_text())
        assert payload["grid_size"] == [32, 32]
        assert "spawn_cell" in payload
        assert "exit_cell" in payload
        assert payload["grid"].startswith("rle-v1:")

    def test_unknown_recipe_returns_structured_error(self, tmp_path: Path) -> None:
        job_dir = tmp_path / "job"
        job_dir.mkdir()
        request_path = job_dir / "request.json"
        result_path = job_dir / "result.json"

        request_path.write_text(
            """{
                "request_id": "test_bad_recipe",
                "recipe_id": "does_not_exist",
                "seed": 1,
                "map_size_tiles": [16, 16],
                "job_dir": "%s",
                "result_path": "%s",
                "status_path": "%s",
                "cancel_path": "%s"
            }"""
            % (
                job_dir,
                result_path,
                job_dir / "status.json",
                job_dir / "cancel.request",
            )
        )

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "bridge.fung_bridge",
                "--request",
                str(request_path),
                "--response",
                str(result_path),
            ],
            cwd=Path(__file__).resolve().parent.parent,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert completed.returncode == 1

        import json

        result = json.loads(result_path.read_text())
        assert result["success"] is False
        assert result["error"]["code"] == "RECIPE_NOT_FOUND"
