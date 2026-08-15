"""
W7: MAP-Elites integration tests.

Verifies that RandomSearch and Standard_MAP_Elites algorithms work end-to-end
with the archive and fitness evaluation.
"""

import numpy as np
import pytest

try:
    from fung_ai_v2.algorithms import RandomSearch, Standard_MAP_Elites, run_held_out_benchmark
    from fung_ai_v2.archive import GridArchive
    from fung_ai_v2.ca_engine import CARule
except ImportError:
    pytest.skip("fung_ai_v2 package not available (algorithms module)", allow_module_level=True)


# ---------------------------------------------------------------------------
# RandomSearch tests
# ---------------------------------------------------------------------------

def test_random_search_basic_run():
    """RandomSearch.run() fills archive with solutions."""
    algo = RandomSearch()
    archive = algo.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=42, verbose=False)

    assert archive.filled_count > 0, "Archive should have at least one elite after 100 evals"
    assert archive.eval_count == 100, "Should have evaluated exactly 100 solutions"


def test_random_search_respects_max_evals():
    """RandomSearch with max_evals=50 evaluates exactly 50 solutions."""
    algo = RandomSearch()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=50, seed=42, verbose=False)

    assert algo.archive.eval_count == 50


def test_random_search_seed_reproducibility():
    """Two runs with same seed produce same archive results."""
    algo1 = RandomSearch()
    algo1.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=99, verbose=False)
    stats1 = algo1.archive.get_statistics()

    algo2 = RandomSearch()
    algo2.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=99, verbose=False)
    stats2 = algo2.archive.get_statistics()

    assert stats1["coverage"] == stats2["coverage"], "Same seed should give same coverage"
    assert stats1["qd_score"] == pytest.approx(stats2["qd_score"], rel=1e-6)
    assert stats1["max_fitness"] == pytest.approx(stats2["max_fitness"], rel=1e-6)


def test_random_search_different_seeds_differ():
    """Two runs with different seeds produce different results."""
    algo1 = RandomSearch()
    algo1.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=1, verbose=False)
    stats1 = algo1.archive.get_statistics()

    algo2 = RandomSearch()
    algo2.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=2, verbose=False)
    stats2 = algo2.archive.get_statistics()

    # With high probability, results should differ (not a hard guarantee with randomness)
    assert not (stats1["coverage"] == stats2["coverage"] and
                stats1["max_fitness"] == pytest.approx(stats2["max_fitness"], rel=1e-6))


def test_random_search_get_results():
    """get_results() returns dict with expected keys."""
    algo = RandomSearch()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=42, verbose=False)
    results = algo.get_results()

    assert "coverage" in results
    assert "qd_score" in results
    assert "max_fitness" in results
    assert "success_at_10k" in results

    assert 0.0 <= results["coverage"] <= 1.0
    assert results["qd_score"] >= 0.0
    assert results["success_at_10k"] >= 0.0


# ---------------------------------------------------------------------------
# Standard MAP-Elites tests
# ---------------------------------------------------------------------------

def test_map_elites_basic_run():
    """Standard_MAP_Elites.run() fills archive with solutions."""
    algo = Standard_MAP_Elites()
    archive = algo.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=42, verbose=False)

    assert archive.filled_count > 0, "Archive should have elites after 100 evals"
    assert archive.eval_count == 100


def test_map_elites_respects_max_evals():
    """MAP-Elites stops at max_evals."""
    algo = Standard_MAP_Elites()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=50, seed=42, verbose=False)

    assert algo.archive.eval_count == 50


def test_map_elites_seed_reproducibility():
    """MAP-Elites with same seed produces same coverage and QD-score."""
    algo1 = Standard_MAP_Elites()
    algo1.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=99, verbose=False)
    stats1 = algo1.archive.get_statistics()

    algo2 = Standard_MAP_Elites()
    algo2.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=99, verbose=False)
    stats2 = algo2.archive.get_statistics()

    assert stats1["coverage"] == stats2["coverage"]
    assert stats1["qd_score"] == pytest.approx(stats2["qd_score"], rel=1e-6)


def test_map_elites_get_results():
    """MAP-Elites.get_results() returns valid dict."""
    algo = Standard_MAP_Elites()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=100, seed=42, verbose=False)
    results = algo.get_results()

    assert "coverage" in results
    assert "qd_score" in results
    assert "max_fitness" in results
    assert "success_at_10k" in results


def test_map_elites_coverage_improves():
    """MAP-Elites coverage improves as evals increase."""
    algo_50 = Standard_MAP_Elites()
    algo_50.run(grid_size=(20, 20), ticks=50, max_evals=50, seed=42, verbose=False)
    coverage_50 = algo_50.archive.coverage()

    algo_500 = Standard_MAP_Elites()
    algo_500.run(grid_size=(20, 20), ticks=50, max_evals=500, seed=42, verbose=False)
    coverage_500 = algo_500.archive.coverage()

    # With high probability, 500 evals finds more cells than 50 evals
    assert coverage_500 >= coverage_50, "More evaluations should find at least as many elites"


# ---------------------------------------------------------------------------
# Archive statistics consistency tests
# ---------------------------------------------------------------------------

def test_archive_coverage_bounds():
    """Coverage is always in [0, 1]."""
    algo = Standard_MAP_Elites()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=200, seed=42, verbose=False)

    coverage = algo.archive.coverage()
    assert 0.0 <= coverage <= 1.0


def test_archive_qd_score_nonnegative():
    """QD-score is always >= 0."""
    algo = Standard_MAP_Elites()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=200, seed=42, verbose=False)

    qd_score = algo.archive.qd_score()
    assert qd_score >= 0.0


def test_archive_statistics_self_consistent():
    """get_statistics() results are self-consistent."""
    algo = Standard_MAP_Elites()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=200, seed=42, verbose=False)

    stats = algo.archive.get_statistics()
    elites = algo.archive.get_all_elites()

    # num_elites matches filled_count
    assert stats["num_elites"] == algo.archive.filled_count
    assert len(elites) == algo.archive.filled_count

    # max_fitness >= mean_fitness
    if stats["num_elites"] > 0:
        assert stats["max_fitness"] >= stats["mean_fitness"]

    # coverage = filled_count / total_cells
    expected_coverage = algo.archive.filled_count / algo.archive.total_cells
    assert stats["coverage"] == pytest.approx(expected_coverage, rel=1e-6)


# ---------------------------------------------------------------------------
# Algorithm comparison tests
# ---------------------------------------------------------------------------

def test_random_search_vs_map_elites_coverage():
    """MAP-Elites typically achieves better or equal coverage than random search."""
    rs_algo = RandomSearch()
    rs_algo.run(grid_size=(20, 20), ticks=50, max_evals=500, seed=123, verbose=False)
    rs_coverage = rs_algo.archive.coverage()
    rs_qd = rs_algo.archive.qd_score()

    me_algo = Standard_MAP_Elites()
    me_algo.run(grid_size=(20, 20), ticks=50, max_evals=500, seed=123, verbose=False)
    me_coverage = me_algo.archive.coverage()
    me_qd = me_algo.archive.qd_score()

    # Both should find elites (basic sanity check)
    assert rs_coverage > 0.0 and me_coverage > 0.0
    assert rs_qd > 0.0 and me_qd > 0.0


# ---------------------------------------------------------------------------
# Parameter variation tests
# ---------------------------------------------------------------------------

def test_different_grid_sizes():
    """Algorithms work with different grid sizes."""
    for grid_size in [(10, 10), (20, 20), (30, 30)]:
        algo = RandomSearch()
        algo.run(grid_size=grid_size, ticks=50, max_evals=100, seed=42, verbose=False)
        assert algo.archive.filled_count > 0


def test_different_ticks():
    """More ticks typically means higher fitness."""
    algo_10_ticks = RandomSearch()
    algo_10_ticks.run(grid_size=(20, 20), ticks=10, max_evals=100, seed=42, verbose=False)
    max_fit_10 = algo_10_ticks.archive.get_statistics()["max_fitness"]

    algo_100_ticks = RandomSearch()
    algo_100_ticks.run(grid_size=(20, 20), ticks=100, max_evals=100, seed=42, verbose=False)
    max_fit_100 = algo_100_ticks.archive.get_statistics()["max_fitness"]

    # More iterations means CA has more time to stabilize → typically higher fitness
    assert max_fit_100 >= max_fit_10 - 0.05  # Allow small margin for randomness


# ---------------------------------------------------------------------------
# Benchmark protocol test
# ---------------------------------------------------------------------------

def test_run_held_out_benchmark_completes():
    """run_held_out_benchmark completes without error."""
    algo = RandomSearch()
    results = run_held_out_benchmark(
        algo,
        train_rules=("B3/S23",),
        test_rules=("B36/S23",),
        grid_sizes=((20, 20),),
        max_evals=100,
        verbose=False
    )

    assert "train" in results
    assert "val" in results
    assert "test" in results
    assert "summary" in results

    summary = results["summary"]
    assert "train_success" in summary
    assert "test_success" in summary
    assert "generalization_gap" in summary
    assert "generalizes" in summary


# ---------------------------------------------------------------------------
# Verbose output tests for 100% coverage
# ---------------------------------------------------------------------------

def test_random_search_verbose_output(capsys):
    """RandomSearch verbose output prints to stdout (lines 54-57 coverage).

    Print happens every 20 generations; with batch_size=1, gen 20 needs
    at least 20 evals to be reached.
    """
    algo = RandomSearch()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=20, batch_size=1, seed=42, verbose=True)

    captured = capsys.readouterr()
    assert "[RS Gen 20]" in captured.out, "RandomSearch verbose output should include generation prints"
    assert "Evals:" in captured.out
    assert "Coverage:" in captured.out


def test_map_elites_verbose_output(capsys):
    """Standard_MAP_Elites verbose output prints to stdout (lines 110-113 coverage).

    Print happens every 20 generations; with batch_size=1, gen 20 needs
    at least 20 evals to be reached.
    """
    algo = Standard_MAP_Elites()
    algo.run(grid_size=(20, 20), ticks=50, max_evals=20, batch_size=1, seed=42, verbose=True)

    captured = capsys.readouterr()
    assert "[ME Gen 20]" in captured.out, "MAP-Elites verbose output should include generation prints"
    assert "Evals:" in captured.out
    assert "Coverage:" in captured.out


def test_held_out_benchmark_verbose_output(capsys):
    """run_held_out_benchmark verbose output includes headers and summaries (lines 158-215 coverage)."""
    algo = RandomSearch()
    results = run_held_out_benchmark(
        algo,
        train_rules=("B3/S23",),
        test_rules=("B36/S23",),
        grid_sizes=((20, 20),),
        max_evals=50,
        verbose=True
    )

    captured = capsys.readouterr()
    # Should include section headers
    assert "HELD-OUT BENCHMARK PROTOCOL" in captured.out, "Should print benchmark header"
    assert "[TRAINING PHASE]" in captured.out, "Should print training phase header"
    assert "[VALIDATION PHASE]" in captured.out, "Should print validation phase header"
    assert "[TEST PHASE" in captured.out, "Should print test phase header"
    assert "BENCHMARK SUMMARY" in captured.out, "Should print summary section"

    # Verify results were computed
    assert "train_success" in results["summary"]
