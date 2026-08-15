"""Per-recipe deterministic fixture tests.

For every recipe in bridge.generation.RECIPES there is a matching
tests/fixtures/requests/<recipe_id>.json GenerationRequest fixture whose
seed + map_size_tiles are a real, empirically-verified combination for that
recipe (see the calibration note at the top of RECIPES in
bridge/generation.py for how these were derived: swept across many
rule_string/density/steps combos, then checked against actual
generate_candidate_grid() output over 30 seeds at the recipe's target map
size before fitness_targets were written).

These tests exercise the real CA pipeline end-to-end (not mocks): they load
the fixture, generate the actual candidate for its seed, and assert the
resulting metrics fall inside the recipe's own fitness_targets ranges. A
recipe whose fitness_targets don't match its real output will fail here.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bridge.generation import (
    RECIPES,
    compute_candidate_metrics,
    generate_candidate_grid,
)
from bridge.schemas import GenerationRequest

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "requests"


def _load_fixture(recipe_id: str) -> GenerationRequest:
    fixture_path = FIXTURES_DIR / f"{recipe_id}.json"
    data = json.loads(fixture_path.read_text())
    return GenerationRequest.from_dict(data)


class TestFixtureCoverage:
    """Every recipe must have a fixture, and vice versa."""

    def test_every_recipe_has_a_fixture_file(self) -> None:
        missing = [
            recipe_id
            for recipe_id in RECIPES
            if not (FIXTURES_DIR / f"{recipe_id}.json").exists()
        ]
        assert not missing, f"Recipes missing fixture files: {missing}"

    def test_every_fixture_file_maps_to_a_known_recipe(self) -> None:
        orphaned = [
            path.stem
            for path in FIXTURES_DIR.glob("*.json")
            if path.stem not in RECIPES
        ]
        assert not orphaned, f"Fixture files with no matching recipe: {orphaned}"

    def test_fixture_request_id_matches_filename(self) -> None:
        for recipe_id in RECIPES:
            request = _load_fixture(recipe_id)
            assert request.recipe_id == recipe_id

    def test_fixture_is_a_valid_generation_request(self) -> None:
        for recipe_id in RECIPES:
            request = _load_fixture(recipe_id)
            request.validate()  # raises ValueError if invalid


class TestRecipeFixtureGeneration:
    """Generate the real candidate for each recipe's fixture seed and check it."""

    @pytest.mark.parametrize("recipe_id", list(RECIPES.keys()))
    def test_fixture_seed_produces_valid_candidate(self, recipe_id: str) -> None:
        recipe = RECIPES[recipe_id]
        request = _load_fixture(recipe_id)
        map_size = tuple(request.map_size_tiles)

        candidate = generate_candidate_grid(request.seed, map_size, recipe)

        assert candidate is not None, (
            f"Recipe '{recipe_id}' fixture (seed={request.seed}, "
            f"map_size={map_size}) produced no valid candidate"
        )

    @pytest.mark.parametrize("recipe_id", list(RECIPES.keys()))
    def test_fixture_grid_dimensions_match_request(self, recipe_id: str) -> None:
        recipe = RECIPES[recipe_id]
        request = _load_fixture(recipe_id)
        width, height = request.map_size_tiles

        candidate = generate_candidate_grid(request.seed, (width, height), recipe)

        assert candidate is not None
        assert candidate.grid.shape == (height, width)

    @pytest.mark.parametrize("recipe_id", list(RECIPES.keys()))
    def test_fixture_spawn_and_exit_are_floor_cells(self, recipe_id: str) -> None:
        recipe = RECIPES[recipe_id]
        request = _load_fixture(recipe_id)
        map_size = tuple(request.map_size_tiles)

        candidate = generate_candidate_grid(request.seed, map_size, recipe)

        assert candidate is not None
        spawn_x, spawn_y = candidate.spawn_cell
        exit_x, exit_y = candidate.exit_cell
        assert candidate.grid[spawn_y, spawn_x] == 0, "spawn_cell must be floor (0), not wall"
        assert candidate.grid[exit_y, exit_x] == 0, "exit_cell must be floor (0), not wall"

    @pytest.mark.parametrize("recipe_id", list(RECIPES.keys()))
    def test_fixture_metrics_within_recipes_own_fitness_targets(self, recipe_id: str) -> None:
        """This is the calibration check: fitness_targets must match reality.

        A recipe whose fitness_targets were guessed rather than measured
        will fail this test even though generation itself succeeds.
        """
        recipe = RECIPES[recipe_id]
        assert recipe.fitness_targets, f"Recipe '{recipe_id}' has no fitness_targets to check"

        request = _load_fixture(recipe_id)
        map_size = tuple(request.map_size_tiles)

        candidate = generate_candidate_grid(request.seed, map_size, recipe)
        assert candidate is not None

        metrics = compute_candidate_metrics(candidate, recipe)

        for metric_name, (lo, hi) in recipe.fitness_targets.items():
            value = metrics[metric_name]
            assert lo <= value <= hi, (
                f"Recipe '{recipe_id}' fixture metric '{metric_name}'={value} "
                f"is outside its own fitness_targets range ({lo}, {hi})"
            )

    @pytest.mark.parametrize("recipe_id", list(RECIPES.keys()))
    def test_fixture_generation_is_deterministic(self, recipe_id: str) -> None:
        """Re-running the same fixture must produce an identical grid."""
        recipe = RECIPES[recipe_id]
        request = _load_fixture(recipe_id)
        map_size = tuple(request.map_size_tiles)

        candidate_a = generate_candidate_grid(request.seed, map_size, recipe)
        candidate_b = generate_candidate_grid(request.seed, map_size, recipe)

        assert candidate_a is not None
        assert candidate_b is not None
        assert candidate_a.spawn_cell == candidate_b.spawn_cell
        assert candidate_a.exit_cell == candidate_b.exit_cell
        assert (candidate_a.grid == candidate_b.grid).all()


class TestRecipesAreDistinct:
    """Sanity check that recipes weren't copy-pasted with only a new id/name."""

    def test_no_two_recipes_share_the_same_rule_density_steps_combo(self) -> None:
        seen: dict[tuple[str, float, int], str] = {}
        duplicates = []
        for recipe_id, recipe in RECIPES.items():
            key = (recipe.rule_string, recipe.initial_density, recipe.steps)
            if key in seen:
                duplicates.append((recipe_id, seen[key], key))
            else:
                seen[key] = recipe_id
        assert not duplicates, f"Recipes with identical (rule, density, steps): {duplicates}"

    def test_recipe_count_is_in_expected_range(self) -> None:
        # v0.1 build plan Phase 3: 12-16 curated built-in recipes.
        assert 12 <= len(RECIPES) <= 16
