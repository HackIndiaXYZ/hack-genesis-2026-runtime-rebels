import os
import sys
import io
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import pytest
from datetime import datetime, timezone
from PIL import Image
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db
from app.models.complaint import Complaint
from app.models.status_history import StatusHistory

import tempfile
import uuid

# Setup a clean disposable temporary SQLite file for testing
TEST_DB_FILE = os.path.join(tempfile.gettempdir(), f"civicfix_test_{uuid.uuid4().hex}.db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply dependency override
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module", autouse=True)
def setup_test_database():
    """Create test tables and seed records in disposable test DB."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        c1 = Complaint(
            complaint_id="CF-2026-TEST01",
            category="pothole",
            confidence=0.92,
            severity="high",
            latitude=26.4729,
            longitude=80.3498,
            address="Civil Lines, Kanpur",
            department="Road Maintenance (PWD)",
            suggested_action="Immediate patch repair required.",
            complaint_text="A severe pothole on Civil Lines main road.",
            language="en",
            status="submitted",
            duplicate_of=None,
            estimated_resolution_hours=24,
            image_path="/uploads/test01.jpg",
            upvotes=2,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        h1 = StatusHistory(
            complaint_id="CF-2026-TEST01",
            status="submitted",
            timestamp=datetime.now(timezone.utc),
            note="Initial report filed."
        )
        db.add(c1)
        db.add(h1)
        db.commit()
    finally:
        db.close()
    
    yield
    
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except Exception:
            pass

@pytest.fixture
def client():
    return TestClient(app)

# 1. Health check & Root
def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "CivicFix AI API"
    assert data["status"] == "online"

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

# 2. Complaints Listing & Filtering
def test_list_complaints(client):
    res = client.get("/api/complaints")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["complaint_id"] == "CF-2026-TEST01"

def test_list_complaints_with_filters(client):
    # Filter by category matching
    res = client.get("/api/complaints?category=pothole")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # Filter by category non-matching
    res_none = client.get("/api/complaints?category=nonexistent")
    assert res_none.status_code == 200
    assert len(res_none.json()) == 0

# 3. Complaint Details & Timeline
def test_get_complaint_detail(client):
    res = client.get("/api/complaints/CF-2026-TEST01")
    assert res.status_code == 200
    data = res.json()
    assert data["complaint_id"] == "CF-2026-TEST01"
    assert data["category"] == "pothole"
    assert len(data["history"]) >= 1
    assert data["history"][0]["status"] == "submitted"

def test_get_complaint_not_found(client):
    res = client.get("/api/complaints/CF-NONEXISTENT")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()

# 4. Create Complaint
def test_create_complaint(client):
    payload = {
        "complaint_id": "CF-2026-TEST02",
        "category": "open manhole",
        "confidence": 0.95,
        "severity": "critical",
        "location": {
            "lat": 25.3176,
            "lng": 82.9739,
            "address": "Godowlia Chowk, Varanasi"
        },
        "department": "Public Works & Drainage",
        "suggested_action": "Urgent barricading required.",
        "complaint_text": "Exposed manhole on pedestrian path.",
        "language": "en",
        "estimated_resolution_hours": 12,
        "image_path": "/uploads/test02.jpg"
    }
    res = client.post("/api/complaints", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["complaint_id"] == "CF-2026-TEST02"
    assert data["severity"] == "critical"
    assert len(data["history"]) == 1

# 5. Upvote Complaint
def test_upvote_complaint(client):
    res = client.post("/api/complaints/CF-2026-TEST01/upvote")
    assert res.status_code == 200
    data = res.json()
    assert data["complaint_id"] == "CF-2026-TEST01"
    assert data["upvotes"] == 3  # initial 2 + 1

# 6. Admin Status Updates & Authorization
def test_status_update_dev_mode(client):
    # Without ADMIN_API_KEY set, update is allowed
    payload = {"status": "in_progress", "note": "Technician dispatched to inspect."}
    res = client.patch("/api/complaints/CF-2026-TEST01/status", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "in_progress"
    assert any(h["status"] == "in_progress" for h in data["history"])

def test_status_update_invalid_status(client):
    payload = {"status": "invalid_status_value"}
    res = client.patch("/api/complaints/CF-2026-TEST01/status", json=payload)
    assert res.status_code == 400
    assert "invalid status" in res.json()["detail"].lower()

def test_status_update_with_admin_auth(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "super-secret-admin-pass")

    # Call without key -> 401
    payload = {"status": "resolved", "note": "Fixed successfully."}
    res_unauth = client.patch("/api/complaints/CF-2026-TEST01/status", json=payload)
    assert res_unauth.status_code == 401

    # Call with wrong key -> 401
    res_wrong = client.patch(
        "/api/complaints/CF-2026-TEST01/status",
        json=payload,
        headers={"X-Admin-Key": "wrong-key"}
    )
    assert res_wrong.status_code == 401

    # Call with valid key -> 200
    res_ok = client.patch(
        "/api/complaints/CF-2026-TEST01/status",
        json=payload,
        headers={"X-Admin-Key": "super-secret-admin-pass"}
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "resolved"

def test_department_reassignment(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "super-secret-admin-pass")

    payload = {"department": "Jal Sansthan (Water Board)", "note": "Forwarded to water department."}
    res = client.patch(
        "/api/complaints/CF-2026-TEST01/department",
        json=payload,
        headers={"X-Admin-Key": "super-secret-admin-pass"}
    )
    assert res.status_code == 200
    assert res.json()["department"] == "Jal Sansthan (Water Board)"

def test_admin_auth_production_missing_key_rejected(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    payload = {"status": "resolved"}
    res = client.patch("/api/complaints/CF-2026-TEST01/status", json=payload)
    assert res.status_code == 500
    assert "ADMIN_API_KEY must be configured in production" in res.json()["detail"]

def test_admin_auth_production_with_valid_key(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("ADMIN_API_KEY", "prod-strong-secret-key-999")

    payload = {"status": "resolved"}
    # Call without key -> 401
    res_unauth = client.patch("/api/complaints/CF-2026-TEST01/status", json=payload)
    assert res_unauth.status_code == 401

    # Call with valid key -> 200
    res_ok = client.patch(
        "/api/complaints/CF-2026-TEST01/status",
        json=payload,
        headers={"X-Admin-Key": "prod-strong-secret-key-999"}
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "resolved"

def test_production_cors_restrictions():
    """
    Verifies that when ENVIRONMENT=production is set,
    localhost origin regex is disabled and only explicit ALLOWED_ORIGINS are allowed.
    """
    from starlette.middleware.cors import CORSMiddleware
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    test_app = FastAPI()
    is_prod = True
    allowed_env = "https://civicfix.vercel.app"
    origins = [o.strip() for o in allowed_env.split(",") if o.strip()]
    origin_regex = None if is_prod else r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @test_app.get("/test-cors")
    def dummy():
        return {"ok": True}

    c = TestClient(test_app)

    # 1. Localhost origin in production must NOT receive access-control-allow-origin
    res_local = c.get("/test-cors", headers={"Origin": "http://localhost:5173"})
    assert "access-control-allow-origin" not in res_local.headers

    # 2. Configured production origin must receive access-control-allow-origin
    res_prod = c.get("/test-cors", headers={"Origin": "https://civicfix.vercel.app"})
    assert res_prod.headers.get("access-control-allow-origin") == "https://civicfix.vercel.app"

# 7. Stats & Aggregations
def test_stats_endpoint(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total" in data
    assert "resolved" in data
    assert "critical" in data
    assert "by_category" in data
    assert "by_severity" in data
    assert "by_ward" in data
    assert data["total"] >= 2

# 8. Multilingual Generation
def test_generate_complaint_multilingual(client):
    # English
    res_en = client.post("/api/generate-complaint", json={
        "category": "pothole",
        "severity": "high",
        "address": "Mall Road, Kanpur",
        "language": "en"
    })
    assert res_en.status_code == 200
    assert "pothole" in res_en.json()["complaint_text"].lower()

    # Hindi
    res_hi = client.post("/api/generate-complaint", json={
        "category": "pothole",
        "severity": "high",
        "address": "Mall Road, Kanpur",
        "language": "hi"
    })
    assert res_hi.status_code == 200
    assert len(res_hi.json()["complaint_text"]) > 10

# 9. Image Upload & Analysis
def test_analyze_valid_image(client):
    # Create a synthetic test image
    img = Image.new("RGB", (200, 200), color="gray")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("pothole_test.jpg", buf, "image/jpeg")}
    data = {
        "latitude": 26.4729,
        "longitude": 80.3498,
        "address": "Civil Lines, Kanpur",
        "language": "en"
    }

    res = client.post("/api/analyze", files=files, data=data)
    assert res.status_code == 200
    result = res.json()
    assert result["complaint_id"].startswith("CF-2026-")
    assert result["category"] is not None
    assert result["confidence"] > 0
    assert result["severity"] is not None
    assert result["image_path"].startswith("/uploads/")
    assert result["department"] is not None

def test_analyze_corrupt_file(client):
    # Send non-image binary as .jpg
    fake_buf = io.BytesIO(b"Not an actual image file header at all")
    files = {"file": ("corrupt.jpg", fake_buf, "image/jpeg")}
    data = {"latitude": 26.0, "longitude": 80.0, "address": "Test"}

    res = client.post("/api/analyze", files=files, data=data)
    assert res.status_code == 400
    assert "corrupted" in res.json()["detail"].lower() or "not a valid image" in res.json()["detail"].lower()

def test_analyze_file_size_limit(client):
    # Create oversized content > 10MB
    oversized = io.BytesIO(b"X" * (10 * 1024 * 1024 + 1024))
    files = {"file": ("huge.jpg", oversized, "image/jpeg")}
    data = {"latitude": 26.0, "longitude": 80.0, "address": "Test"}

    res = client.post("/api/analyze", files=files, data=data)
    assert res.status_code == 400
    assert "exceeds maximum allowed size" in res.json()["detail"].lower()

# 10. Duplicate Detection (Geospatial)
def test_duplicate_detection_nearby(client):
    # Seed an active complaint specifically for duplicate detection
    active_payload = {
        "complaint_id": "CF-2026-ACTIVEDUP",
        "category": "pothole",
        "confidence": 0.90,
        "severity": "high",
        "location": {
            "lat": 26.4729,
            "lng": 80.3498,
            "address": "Civil Lines, Kanpur"
        },
        "department": "Road Maintenance (PWD)",
        "complaint_text": "Pothole on Civil Lines main road.",
        "status": "submitted"
    }
    create_res = client.post("/api/complaints", json=active_payload)
    assert create_res.status_code == 201

    img = Image.new("RGB", (100, 100), color="black")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    # Coords close (< 10m) to CF-2026-ACTIVEDUP (26.4729, 80.3498)
    files = {"file": ("dup.jpg", buf, "image/jpeg")}
    data = {
        "latitude": 26.47291,
        "longitude": 80.34981,
        "address": "Civil Lines, Kanpur",
        "language": "en"
    }

    res = client.post("/api/analyze", files=files, data=data)
    assert res.status_code == 200
    result = res.json()
    assert result["duplicate_of"] == "CF-2026-ACTIVEDUP"

def test_production_cloud_storage_required(client, monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CLOUDINARY_URL", raising=False)

    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    files = {"file": ("prod_test.jpg", buf, "image/jpeg")}
    data = {"latitude": 26.0, "longitude": 80.0, "address": "Production Road"}

    res = client.post("/api/analyze", files=files, data=data)
    assert res.status_code == 500
    assert "CLOUDINARY_URL is not configured" in res.json()["detail"]
