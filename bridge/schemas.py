"""Typed request/result/error models for the bridge protocol."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field
from typing import Any, Optional
from datetime import datetime, timezone


@dataclass
class GenerationRequest:
    """Generation request from Godot to Python bridge."""
    protocol_version: int = 1
    request_id: str = ""
    generator_version: str = "0.1.0"
    recipe_id: str = ""
    seed: int = 0
    map_size_tiles: list[int] = field(default_factory=lambda: [96, 96])
    tile_size_px: list[int] = field(default_factory=lambda: [16, 16])
    generation_budget: str = "balanced"
    environment_mode: str = "manual_preset"
    environment_preset: str = "limestone_cave"
    overrides: dict[str, Any] = field(default_factory=dict)
    candidate_count: int = 24
    job_dir: str = ""
    result_path: str = ""
    status_path: str = ""
    cancel_path: str = ""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> GenerationRequest:
        """Construct from dictionary (JSON-deserialized)."""
        return GenerationRequest(**{k: v for k, v in data.items() if hasattr(GenerationRequest, k)})

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def validate(self) -> None:
        """Validate request fields."""
        if not self.request_id:
            raise ValueError("request_id is required")
        if not self.recipe_id:
            raise ValueError("recipe_id is required")
        if self.seed < 0:
            raise ValueError("seed must be non-negative")
        if len(self.map_size_tiles) != 2 or any(s <= 0 for s in self.map_size_tiles):
            raise ValueError("map_size_tiles must be [width, height] with positive values")
        if self.candidate_count < 1:
            raise ValueError("candidate_count must be >= 1")


@dataclass
class Candidate:
    """A single generated candidate."""
    candidate_id: str
    seed: int
    valid: bool
    preview_path: str
    payload_path: str
    metrics: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class GenerationResult:
    """Result from Python bridge back to Godot."""
    request_id: str = ""
    success: bool = False
    generator_version: str = "0.1.0"
    recipe_id: str = ""
    seed: int = 0
    candidates: list[Candidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "generator_version": self.generator_version,
            "recipe_id": self.recipe_id,
            "seed": self.seed,
            "candidates": [c.to_dict() for c in self.candidates],
            "warnings": self.warnings,
            "errors": self.errors,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> GenerationResult:
        """Construct from dictionary (JSON-deserialized)."""
        result = GenerationResult(
            request_id=data.get("request_id", ""),
            success=data.get("success", False),
            generator_version=data.get("generator_version", "0.1.0"),
            recipe_id=data.get("recipe_id", ""),
            seed=data.get("seed", 0),
            warnings=data.get("warnings", []),
            errors=data.get("errors", []),
        )
        for cand_data in data.get("candidates", []):
            candidate = Candidate(
                candidate_id=cand_data.get("candidate_id", ""),
                seed=cand_data.get("seed", 0),
                valid=cand_data.get("valid", False),
                preview_path=cand_data.get("preview_path", ""),
                payload_path=cand_data.get("payload_path", ""),
                metrics=cand_data.get("metrics", {}),
                tags=cand_data.get("tags", []),
            )
            result.candidates.append(candidate)
        return result


@dataclass
class BridgeError:
    """Structured error response."""
    code: str = ""
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    action: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_result_dict(self, request_id: str) -> dict[str, Any]:
        """Convert to a result dictionary for error responses."""
        return {
            "request_id": request_id,
            "success": False,
            "error": self.to_dict(),
            "candidates": [],
            "warnings": [],
            "errors": [self.message],
        }


@dataclass
class StatusUpdate:
    """Status file that Python writes during generation."""
    protocol_version: int = 1
    request_id: str = ""
    state: str = "queued"
    progress: float = 0.0
    stage: str = ""
    message: str = ""
    updated_utc: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @staticmethod
    def now() -> str:
        """Get current UTC timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()
