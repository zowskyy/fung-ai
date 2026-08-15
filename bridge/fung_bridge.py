"""Local JSON-file bridge CLI: receives generation requests, runs generation, writes results."""
from __future__ import annotations

import argparse
import traceback
from pathlib import Path

from bridge.generation import (
    RECIPES,
    generate_candidate_grid,
    compute_candidate_metrics,
    tags_from_metrics,
)
from bridge.schemas import GenerationRequest, GenerationResult, StatusUpdate, BridgeError, Candidate
from bridge.manifest_writer import atomic_write_json, read_json, ensure_dir


def write_status(
    status_path: str | Path,
    request_id: str,
    state: str,
    progress: float,
    stage: str,
    message: str = "",
) -> None:
    """Write status file atomically."""
    status_data = {
        "protocol_version": 1,
        "request_id": request_id,
        "state": state,
        "progress": min(1.0, max(0.0, progress)),
        "stage": stage,
        "message": message,
        "updated_utc": StatusUpdate.now(),
    }
    atomic_write_json(status_path, status_data)


def generate_candidates(request: GenerationRequest) -> GenerationResult:
    """Generate candidates using fung_ai_v2 engine."""
    from fung_ai_v2 import __version__ as fung_version

    # Write initial status
    write_status(request.status_path, request.request_id, "running", 0.05, "initializing")

    # Validate recipe exists
    if request.recipe_id not in RECIPES:
        raise BridgeError(
            code="RECIPE_NOT_FOUND",
            message=f"Recipe '{request.recipe_id}' not found",
            details={"recipe_id": request.recipe_id, "available": list(RECIPES.keys())},
            action="Select a recipe from the available list",
        )

    recipe = RECIPES[request.recipe_id]

    # Determine candidate count based on budget
    budget_counts = {"fast": 3, "balanced": 6, "thorough": 12}
    actual_count = budget_counts.get(request.generation_budget, 6)

    result = GenerationResult(
        request_id=request.request_id,
        success=True,
        generator_version=fung_version,
        recipe_id=request.recipe_id,
        seed=request.seed,
        candidates=[],
        warnings=[],
        errors=[],
    )

    # Generate candidates
    valid_count = 0
    for i in range(actual_count):
        candidate_seed = request.seed + i
        candidate_id = f"candidate_{i + 1:03d}"

        # Generate grid
        progress = 0.1 + (i / max(1, actual_count)) * 0.7
        grid = generate_candidate_grid(
            candidate_seed,
            tuple(request.map_size_tiles),
            recipe,
            lambda p, msg: write_status(
                request.status_path,
                request.request_id,
                "running",
                progress + p * 0.05,
                "generating",
                msg,
            ),
        )

        if grid is None:
            continue  # Invalid candidate, skip

        valid_count += 1
        metrics = compute_candidate_metrics(grid)
        tags = tags_from_metrics(metrics)

        candidate = Candidate(
            candidate_id=candidate_id,
            seed=candidate_seed,
            valid=True,
            preview_path=f"previews/{candidate_id}.png",
            payload_path=f"candidates/{candidate_id}.json",
            metrics=metrics,
            tags=tags,
        )
        result.candidates.append(candidate)

    if not result.candidates:
        result.warnings.append(
            f"No valid candidates generated (attempted {actual_count}). Try different parameters."
        )

    return result


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Fung local bridge: process generation requests")
    parser.add_argument("--request", required=True, help="Path to request.json")
    parser.add_argument("--response", required=True, help="Path to write result.json")
    args = parser.parse_args()

    request_path = Path(args.request).resolve()
    response_path = Path(args.response).resolve()

    try:
        # Load and validate request
        if not request_path.exists():
            raise FileNotFoundError(f"Request file not found: {request_path}")

        request_data = read_json(request_path)
        request = GenerationRequest.from_dict(request_data)
        request.validate()

        # Resolve paths
        job_dir = Path(request.job_dir).resolve()
        status_path = Path(request.status_path).resolve()
        cancel_path = Path(request.cancel_path).resolve()

        # Create job directories
        ensure_dir(job_dir / "candidates")
        ensure_dir(job_dir / "previews")

        # Generate
        write_status(status_path, request.request_id, "running", 0.02, "initializing")

        result = generate_candidates(request)

        # Check for cancellation
        if cancel_path.exists():
            write_status(status_path, request.request_id, "cancelled", 1.0, "cancelled")
            error_result = {
                "request_id": request.request_id,
                "success": False,
                "candidates": [],
                "warnings": [],
                "errors": ["Generation was cancelled"],
            }
            atomic_write_json(response_path, error_result)
            return 2

        # Write result atomically
        atomic_write_json(response_path, result.to_dict())
        write_status(status_path, request.request_id, "completed", 1.0, "complete")
        return 0

    except BridgeError as exc:
        req_id = request.request_id if "request" in locals() else "unknown"
        write_status(status_path, req_id, "failed", 1.0, "error", exc.message)
        atomic_write_json(response_path, exc.to_result_dict(req_id))
        return 1

    except Exception as exc:  # noqa: BLE001
        # Log full traceback
        if "request" in locals():
            log_path = Path(request.job_dir) / "job.log"
            ensure_dir(log_path.parent)
            with open(log_path, "w") as f:
                f.write(traceback.format_exc())
            write_status(
                Path(request.status_path),
                request.request_id,
                "failed",
                1.0,
                "error",
                str(exc),
            )
            error_result = {
                "request_id": request.request_id,
                "success": False,
                "error": {
                    "code": "BRIDGE_ERROR",
                    "message": str(exc),
                    "details": {"type": type(exc).__name__},
                    "action": "Check the job.log file for details",
                },
                "candidates": [],
                "warnings": [],
                "errors": [str(exc)],
            }
            atomic_write_json(response_path, error_result)
        else:
            error_result = {
                "request_id": "unknown",
                "success": False,
                "error": {
                    "code": "BRIDGE_ERROR",
                    "message": str(exc),
                    "details": {},
                    "action": "Check the bridge logs",
                },
                "candidates": [],
                "warnings": [],
                "errors": [str(exc)],
            }
            atomic_write_json(response_path, error_result)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
