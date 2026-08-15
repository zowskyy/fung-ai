"""Local JSON-file bridge CLI: receives generation requests, runs generation, writes results."""
from __future__ import annotations

import argparse
import traceback
from pathlib import Path

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
    import random
    from fung_ai_v2 import __version__ as fung_version

    # Write initial status
    write_status(request.status_path, request.request_id, "running", 0.05, "initializing")

    # For v0.1: stub implementation that creates a few deterministic candidates
    # TODO: Integrate actual fung_ai_v2 generation engine
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

    # Generate stub candidates
    random.seed(request.seed)
    for i in range(min(request.candidate_count, 3)):  # v0.1: stub 3 candidates
        candidate_seed = request.seed + i
        candidate_id = f"candidate_{i+1:03d}"

        # Write progress
        progress = 0.1 + (i / max(1, request.candidate_count)) * 0.8
        msg = f"Generated {i + 1}/{request.candidate_count}"
        write_status(
            request.status_path,
            request.request_id,
            "running",
            progress,
            "generating",
            msg,
        )

        # Create candidate
        candidate = Candidate(
            candidate_id=candidate_id,
            seed=candidate_seed,
            valid=True,
            preview_path=f"previews/{candidate_id}.png",
            payload_path=f"candidates/{candidate_id}.json",
            metrics={
                "walkable_ratio": 0.40 + random.random() * 0.2,
                "path_length": int(50 + random.random() * 50),
                "loop_count": random.randint(1, 5),
                "branch_count": random.randint(3, 12),
                "open_space_score": 0.4 + random.random() * 0.4,
                "score": 0.7 + random.random() * 0.25,
            },
            tags=random.sample([
                "Long Route", "Short Run", "Open Chambers", "Tight Tunnels",
                "Many Loops", "Branching", "Linear", "Arena-Friendly",
                "Exploration-Focused", "Chokepoint Heavy"
            ], k=3),
        )
        result.candidates.append(candidate)

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
