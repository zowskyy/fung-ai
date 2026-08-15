"""Tests for bridge protocol schemas and validators."""
import pytest
from bridge.schemas import GenerationRequest, GenerationResult, Candidate, BridgeError, StatusUpdate


class TestGenerationRequest:
    """Test request schema validation."""

    def test_valid_request(self) -> None:
        """A valid request should construct and validate."""
        request = GenerationRequest(
            request_id="test_001",
            recipe_id="compact_roguelike_rooms",
            seed=12345,
            map_size_tiles=[96, 96],
            job_dir="/tmp/fung/jobs/test_001",
            result_path="/tmp/fung/jobs/test_001/result.json",
            status_path="/tmp/fung/jobs/test_001/status.json",
            cancel_path="/tmp/fung/jobs/test_001/cancel.request",
        )
        request.validate()  # Should not raise

    def test_missing_request_id(self) -> None:
        """Request without request_id should fail validation."""
        request = GenerationRequest(recipe_id="test", seed=0)
        with pytest.raises(ValueError, match="request_id"):
            request.validate()

    def test_negative_seed(self) -> None:
        """Request with negative seed should fail validation."""
        request = GenerationRequest(request_id="test", recipe_id="test", seed=-1)
        with pytest.raises(ValueError, match="seed"):
            request.validate()

    def test_invalid_map_size(self) -> None:
        """Request with invalid map_size should fail validation."""
        request = GenerationRequest(
            request_id="test",
            recipe_id="test",
            seed=0,
            map_size_tiles=[0, 0],
        )
        with pytest.raises(ValueError, match="map_size_tiles"):
            request.validate()

    def test_request_from_dict(self) -> None:
        """Request should construct from dictionary."""
        data = {
            "protocol_version": 1,
            "request_id": "test_001",
            "generator_version": "0.1.0",
            "recipe_id": "compact_roguelike_rooms",
            "seed": 12345,
            "map_size_tiles": [96, 96],
            "tile_size_px": [16, 16],
            "generation_budget": "balanced",
            "candidate_count": 24,
        }
        request = GenerationRequest.from_dict(data)
        assert request.request_id == "test_001"
        assert request.recipe_id == "compact_roguelike_rooms"
        assert request.seed == 12345


class TestCandidate:
    """Test candidate schema."""

    def test_candidate_creation(self) -> None:
        """Candidate should construct and serialize."""
        candidate = Candidate(
            candidate_id="cand_001",
            seed=12345,
            valid=True,
            preview_path="previews/cand_001.png",
            payload_path="candidates/cand_001.json",
            metrics={"walkable_ratio": 0.5, "path_length": 50},
            tags=["Long Route", "Open Chambers"],
        )
        data = candidate.to_dict()
        assert data["candidate_id"] == "cand_001"
        assert data["metrics"]["walkable_ratio"] == 0.5
        assert "Long Route" in data["tags"]


class TestGenerationResult:
    """Test result schema."""

    def test_result_creation(self) -> None:
        """Result should construct with candidates."""
        result = GenerationResult(
            request_id="test_001",
            success=True,
            recipe_id="compact_roguelike_rooms",
            seed=12345,
        )
        candidate = Candidate(
            candidate_id="cand_001",
            seed=12345,
            valid=True,
            preview_path="previews/cand_001.png",
            payload_path="candidates/cand_001.json",
        )
        result.candidates.append(candidate)

        data = result.to_dict()
        assert data["success"] is True
        assert len(data["candidates"]) == 1
        assert data["candidates"][0]["candidate_id"] == "cand_001"

    def test_result_from_dict(self) -> None:
        """Result should construct from dictionary."""
        data = {
            "request_id": "test_001",
            "success": True,
            "generator_version": "0.1.0",
            "recipe_id": "compact_roguelike_rooms",
            "seed": 12345,
            "candidates": [
                {
                    "candidate_id": "cand_001",
                    "seed": 12345,
                    "valid": True,
                    "preview_path": "previews/cand_001.png",
                    "payload_path": "candidates/cand_001.json",
                    "metrics": {},
                    "tags": [],
                }
            ],
            "warnings": [],
            "errors": [],
        }
        result = GenerationResult.from_dict(data)
        assert result.success is True
        assert len(result.candidates) == 1


class TestBridgeError:
    """Test error schema."""

    def test_error_to_result(self) -> None:
        """Error should convert to result dictionary."""
        error = BridgeError(
            code="RECIPE_NOT_FOUND",
            message="Recipe not found",
            details={"recipe_id": "unknown"},
            action="Use a valid recipe ID",
        )
        result_data = error.to_result_dict("test_001")
        assert result_data["success"] is False
        assert result_data["error"]["code"] == "RECIPE_NOT_FOUND"
        assert result_data["request_id"] == "test_001"


class TestStatusUpdate:
    """Test status schema."""

    def test_status_creation(self) -> None:
        """Status should construct and serialize."""
        status = StatusUpdate(
            request_id="test_001",
            state="running",
            progress=0.5,
            stage="generating",
            message="Generating candidates",
        )
        data = status.to_dict()
        assert data["state"] == "running"
        assert data["progress"] == 0.5

    def test_status_timestamp(self) -> None:
        """Status should generate ISO 8601 timestamp."""
        timestamp = StatusUpdate.now()
        assert "T" in timestamp  # ISO format includes T
        assert "Z" in timestamp or "+" in timestamp  # Timezone info
