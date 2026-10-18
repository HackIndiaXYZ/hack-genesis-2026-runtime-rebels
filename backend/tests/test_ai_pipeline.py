import os
import sys
import io
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

# Ensure backend and root are on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent
for p in [str(BACKEND_DIR), str(ROOT_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.ai_pipeline import (
    normalize_category,
    run_ai_pipeline,
    fallback_detector,
    DEPARTMENT_MAPPING,
    SUGGESTED_ACTIONS,
    RESOLUTION_HOURS
)

@pytest.fixture
def sample_image_path(tmp_path):
    """Creates a temporary valid JPEG image for pipeline tests."""
    img_path = tmp_path / "test_pothole.jpg"
    img = Image.new("RGB", (300, 300), color=(128, 128, 128))
    img.save(img_path, format="JPEG")
    return str(img_path)

# 1. Category Mapping & Normalization Tests
def test_category_normalization():
    assert normalize_category("pothole") == "pothole"
    assert normalize_category("open_manhole") == "open manhole"
    assert normalize_category("open manhole") == "open manhole"
    assert normalize_category("manhole") == "open manhole"
    assert normalize_category("overflowing_garbage") == "overflowing garbage"
    assert normalize_category("garbage") == "overflowing garbage"
    assert normalize_category("broken_streetlight") == "broken streetlight"
    assert normalize_category("water_leakage") == "water leakage"
    assert normalize_category("damaged_road_sign") == "damaged road sign"
    assert normalize_category("crack") == "crack"
    assert normalize_category("alligator_crack") == "alligator crack"
    assert normalize_category("alligator-crack") == "alligator crack"
    assert normalize_category("hallucinated_category") == "unknown"
    assert normalize_category(None) == "unknown"
    assert normalize_category("") == "unknown"

# 2. Model Weight Files Inspection
def test_model_weight_files_exist():
    v3_weights = ROOT_DIR / "civicfix_v3_best.pt"
    old_weights = ROOT_DIR / "civic_best.pt"

    assert v3_weights.exists(), "civicfix_v3_best.pt must exist in repository root"
    assert v3_weights.stat().st_size > 10 * 1024 * 1024, "civicfix_v3_best.pt size should be > 10MB"

    assert old_weights.exists(), "civic_best.pt must exist in repository root"
    assert old_weights.stat().st_size > 5 * 1024 * 1024, "civic_best.pt size should be > 5MB"

import asyncio

# 3. Missing Credentials Handling
def test_pipeline_missing_gemini_key(sample_image_path, monkeypatch):
    """When GEMINI_API_KEY is unset, pipeline must not crash and should use safe fallback."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    res = asyncio.run(run_ai_pipeline(
        image_abs_path=sample_image_path,
        lat=26.4729,
        lng=80.3498,
        address="Civil Lines, Kanpur",
        language="en"
    ))

    assert res["complaint_id"].startswith("CF-2026-")
    assert res["category"] is not None
    assert res["confidence"] > 0
    assert res["location"]["address"] == "Civil Lines, Kanpur"
    assert res["raw_vlm"] is None
    assert res["consensus_mode"] in ("yolo_only", "lightweight_fallback")

# 4. Gemini API Failure / Rate Limit Resilience
def test_pipeline_gemini_api_error_resilience(sample_image_path, monkeypatch):
    """When Gemini raises a network error or rate limit, pipeline recovers gracefully."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")

    with patch("intelligence.vlm_analyze", side_effect=RuntimeError("503 Service Unavailable")):
        res = asyncio.run(run_ai_pipeline(
            image_abs_path=sample_image_path,
            lat=26.4729,
            lng=80.3498,
            address="Civil Lines, Kanpur"
        ))

        assert res["complaint_id"].startswith("CF-2026-")
        assert res["category"] is not None
        assert res["raw_vlm"] is None

# 5. Untrusted Gemini Output Validation
def test_pipeline_untrusted_gemini_output(sample_image_path, monkeypatch):
    """Validates that hallucinated categories or malformed outputs from Gemini are sanitized."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")

    mock_vlm = {
        "ok": True,
        "category": "alien_spacecraft_debris",
        "confidence": 0.99,
        "severity": "SuperCritical",
        "description": "Unearthly object detected."
    }

    with patch("intelligence.vlm_analyze", return_value=mock_vlm):
        res = asyncio.run(run_ai_pipeline(
            image_abs_path=sample_image_path,
            lat=26.4729,
            lng=80.3498,
            address="Civil Lines, Kanpur"
        ))

        # The hallucinated category must be mapped to 'unknown' or fallback
        assert res["category"] in ("unknown", "pothole")
        # Department must use a valid municipal department fallback
        assert res["department"] in ("Municipal Public Works", "Road Maintenance (PWD)")

# 6. Consensus: Agreement Between YOLO & Gemini
def test_consensus_agreement(sample_image_path, monkeypatch):
    """When YOLO and VLM agree on 'pothole', consensus confirms detection with conservative severity."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")

    mock_yolo_ret = {
        "found": True,
        "primary": {
            "category": "pothole",
            "confidence": 0.91,
            "severity_label": "High",
            "box": [10.0, 10.0, 100.0, 100.0]
        },
        "detections": [{"category": "pothole", "confidence": 0.91}]
    }

    mock_vlm_ret = {
        "ok": True,
        "category": "pothole",
        "confidence": 0.88,
        "severity": "Medium",
        "description": "Deep asphalt depression with jagged perimeter."
    }

    with patch("app.services.ai_pipeline.vision", MagicMock(analyze_image=MagicMock(return_value=mock_yolo_ret))), \
         patch("intelligence.vlm_analyze", return_value=mock_vlm_ret):

        res = asyncio.run(run_ai_pipeline(
            image_abs_path=sample_image_path,
            lat=26.4729,
            lng=80.3498,
            address="Civil Lines, Kanpur"
        ))

        assert res["category"] == "pothole"
        assert res["confidence"] == 0.91  # Raw YOLO confidence preserved
        assert res["severity"] == "high"  # Conservative maximum
        assert res["needs_review"] is False
        assert res["consensus_mode"] == "yolo_vlm_consensus"

# 7. Consensus: Disagreement Between YOLO & Gemini
def test_consensus_disagreement(sample_image_path, monkeypatch):
    """When YOLO reports pothole but VLM reports open manhole, conflict requires human review."""
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")

    mock_yolo_ret = {
        "found": True,
        "primary": {
            "category": "pothole",
            "confidence": 0.85,
            "severity_label": "High",
            "box": [10.0, 10.0, 100.0, 100.0]
        },
        "detections": []
    }

    mock_vlm_ret = {
        "ok": True,
        "category": "open_manhole",
        "confidence": 0.88,
        "severity": "High",
        "description": "Circular opening without cover on walkway."
    }

    with patch("app.services.ai_pipeline.vision", MagicMock(analyze_image=MagicMock(return_value=mock_yolo_ret))), \
         patch("intelligence.vlm_analyze", return_value=mock_vlm_ret):

        res = asyncio.run(run_ai_pipeline(
            image_abs_path=sample_image_path,
            lat=26.4729,
            lng=80.3498,
            address="Civil Lines, Kanpur"
        ))

        # Disagreement flag must be active
        assert res["needs_review"] is True
        assert "disagreement" in res["review_reason"].lower()
        assert res["consensus_mode"] == "yolo_vlm_consensus"

# 8. User Location Strictly Preserved (Never Hallucinated)
def test_user_location_preserved(sample_image_path, monkeypatch):
    """Verifies that user-supplied lat/lng/address are never overridden by AI inference."""
    user_lat = 25.3176
    user_lng = 82.9739
    user_addr = "Assi Ghat, Varanasi, UP, India"

    res = asyncio.run(run_ai_pipeline(
        image_abs_path=sample_image_path,
        lat=user_lat,
        lng=user_lng,
        address=user_addr,
        language="hi"
    ))

    assert res["location"]["lat"] == user_lat
    assert res["location"]["lng"] == user_lng
    assert res["location"]["address"] == user_addr
    assert user_addr in res["complaint_text"]
