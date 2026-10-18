import os
import sys
import json
import sqlite3
import httpx
from pathlib import Path
from PIL import Image
import io

BACKEND_BASE = "http://127.0.0.1:8000"
FRONTEND_BASE = "http://localhost:5173"
ADMIN_KEY = "test_admin_secret_key_2026"
DB_PATH = Path("backend/civicfix_e2e_test.db")

results = []

def record(test_name: str, passed: bool, details: str):
    results.append({"test": test_name, "passed": passed, "details": details})
    mark = "PASS" if passed else "FAIL"
    print(f"[{mark}] {test_name}: {details}")

def main():
    print("=" * 70)
    print("CIVICFIX AI — PHASE 7 END-TO-END INTEGRATION TEST SUITE")
    print("=" * 70)

    # 1. Landing Page & Statistics
    try:
        r_fe = httpx.get(f"{FRONTEND_BASE}/", timeout=10)
        assert r_fe.status_code == 200, f"Frontend returned {r_fe.status_code}"
        
        r_stats = httpx.get(f"{BACKEND_BASE}/api/stats", timeout=10)
        assert r_stats.status_code == 200, f"Stats returned {r_stats.status_code}"
        stats = r_stats.json()
        assert stats["total"] >= 23, f"Expected total >= 23, got {stats['total']}"
        assert "resolved" in stats and "avg_resolution_hours" in stats
        record("Workflow 1: Landing Page & Live Statistics", True, f"Frontend 200 OK. Total: {stats['total']}, Resolved: {stats['resolved']}, SLA: {stats['avg_resolution_hours']}h")
    except Exception as e:
        record("Workflow 1: Landing Page & Live Statistics", False, str(e))

    # 2. Upload Valid Image and Verify Analysis Response
    test_cid = None
    saved_rel_path = None
    try:
        # Create a genuine test JPEG image with PIL
        img_buf = io.BytesIO()
        test_img = Image.new("RGB", (640, 480), color=(120, 100, 80))
        test_img.save(img_buf, format="JPEG")
        img_bytes = img_buf.getvalue()

        files = {"file": ("e2e_test_pothole.jpg", img_bytes, "image/jpeg")}
        data = {
            "latitude": "26.4729",
            "longitude": "80.3498",
            "address": "Civil Lines, Kanpur, Uttar Pradesh",
            "language": "en"
        }
        r_ana = httpx.post(f"{BACKEND_BASE}/api/analyze", files=files, data=data, timeout=15)
        assert r_ana.status_code == 200, f"Analysis failed with {r_ana.status_code}: {r_ana.text}"
        ana = r_ana.json()
        test_cid = ana["complaint_id"]
        saved_rel_path = ana["image_path"]
        assert ana["category"] in ["pothole", "crack", "open manhole", "overflowing garbage", "broken streetlight", "water leakage", "damaged road sign"]
        assert 0.0 <= ana["confidence"] <= 1.0
        assert ana["department"] != ""
        assert ana["estimated_resolution_hours"] > 0
        record("Workflow 2: Image Upload & AI Analysis", True, f"Draft ID: {test_cid}, Category: {ana['category']}, Mode: {ana.get('consensus_mode')}, Image: {saved_rel_path}")
    except Exception as e:
        record("Workflow 2: Image Upload & AI Analysis", False, str(e))

    # 3. Submit Complaint and Verify Persistence
    try:
        complaint_payload = {
            "complaint_id": test_cid,
            "category": ana["category"],
            "confidence": ana["confidence"],
            "severity": ana["severity"],
            "location": ana["location"],
            "department": ana["department"],
            "suggested_action": ana["suggested_action"],
            "complaint_text": ana["complaint_text"],
            "language": "en",
            "estimated_resolution_hours": ana["estimated_resolution_hours"],
            "image_path": ana["image_path"]
        }
        r_sub = httpx.post(f"{BACKEND_BASE}/api/complaints", json=complaint_payload, timeout=10)
        assert r_sub.status_code == 201, f"Submission failed with {r_sub.status_code}: {r_sub.text}"
        sub = r_sub.json()
        assert sub["complaint_id"] == test_cid
        assert sub["status"] == "submitted"

        # Check DB directly
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT complaint_id, category, status FROM complaints WHERE complaint_id = ?", (test_cid,))
        row = cur.fetchone()
        assert row is not None, "Complaint row not found in DB"
        cur.execute("SELECT status, note FROM status_history WHERE complaint_id = ?", (test_cid,))
        h_row = cur.fetchone()
        assert h_row is not None, "Initial status history not found in DB"
        con.close()

        record("Workflow 3: Submit Complaint & Database Persistence", True, f"Complaint {test_cid} saved with status '{row[2]}' and initial history note.")
    except Exception as e:
        record("Workflow 3: Submit Complaint & Database Persistence", False, str(e))

    # 4. Track Complaint by ID and Direct URL
    try:
        r_get = httpx.get(f"{BACKEND_BASE}/api/complaints/{test_cid}", timeout=10)
        assert r_get.status_code == 200, f"Get complaint returned {r_get.status_code}"
        details = r_get.json()
        assert details["complaint_id"] == test_cid

        r_fe_track = httpx.get(f"{FRONTEND_BASE}/track?id={test_cid}", timeout=10)
        assert r_fe_track.status_code == 200, f"Frontend track returned {r_fe_track.status_code}"

        record("Workflow 4: Track Complaint by ID & Direct URL", True, f"Details fetched successfully. Direct URL: /track?id={test_cid} returns 200 OK.")
    except Exception as e:
        record("Workflow 4: Track Complaint by ID & Direct URL", False, str(e))

    # 5. Verify Complaint Details, Location, Evidence Image, & History
    try:
        assert details["location"]["address"] == "Civil Lines, Kanpur, Uttar Pradesh"
        assert len(details["history"]) >= 1, "Status history should contain at least 1 record"
        
        # Verify evidence image retrieval via backend static mount
        clean_img = details["image_path"].lstrip("/")
        r_img = httpx.get(f"{BACKEND_BASE}/{clean_img}", timeout=10)
        assert r_img.status_code == 200, f"Image fetch returned {r_img.status_code}"
        assert "image" in r_img.headers.get("content-type", "")

        # Verify image retrieval via frontend proxy
        r_img_proxy = httpx.get(f"{FRONTEND_BASE}/{clean_img}", timeout=10)
        assert r_img_proxy.status_code == 200, f"Proxy image fetch returned {r_img_proxy.status_code}"

        record("Workflow 5: Verification of Details, Location, Image & History", True, f"Address: {details['location']['address']}, History count: {len(details['history'])}, Image retrieval: 200 OK directly and via proxy.")
    except Exception as e:
        record("Workflow 5: Verification of Details, Location, Image & History", False, str(e))

    # 6. Test Map Markers & Category/Severity Filters
    try:
        r_map_fe = httpx.get(f"{FRONTEND_BASE}/map", timeout=10)
        assert r_map_fe.status_code == 200

        r_filter = httpx.get(f"{BACKEND_BASE}/api/complaints?category={ana['category']}&severity={ana['severity']}&status=submitted", timeout=10)
        assert r_filter.status_code == 200
        filtered_list = r_filter.json()
        assert any(c["complaint_id"] == test_cid for c in filtered_list), "Newly created complaint should appear in filtered query"

        record("Workflow 6: Map Page & Filter Queries", True, f"Filter returned {len(filtered_list)} matching items including {test_cid}. /map page loads 200 OK.")
    except Exception as e:
        record("Workflow 6: Map Page & Filter Queries", False, str(e))

    # 7. Upvote Complaint & Persist Count
    try:
        r_up = httpx.post(f"{BACKEND_BASE}/api/complaints/{test_cid}/upvote", timeout=10)
        assert r_up.status_code == 200, f"Upvote returned {r_up.status_code}"
        up_data = r_up.json()
        assert up_data["upvotes"] == 1, f"Expected 1 upvote, got {up_data['upvotes']}"

        # Verify persistent in fresh fetch
        r_check = httpx.get(f"{BACKEND_BASE}/api/complaints/{test_cid}", timeout=10)
        assert r_check.json()["upvotes"] == 1, "Upvote count did not persist in complaint details"

        record("Workflow 7: Upvoting & Persistence", True, f"Upvote count incremented to {up_data['upvotes']} and persisted across requests.")
    except Exception as e:
        record("Workflow 7: Upvoting & Persistence", False, str(e))

    # 8. Admin Status Updates and Department Reassignment
    try:
        # Reassign department
        r_dept = httpx.patch(
            f"{BACKEND_BASE}/api/complaints/{test_cid}/department",
            json={"department": "Road Maintenance (PWD)", "note": "Reassigned to PWD Taskforce 3"},
            headers={"X-Admin-Key": ADMIN_KEY},
            timeout=10
        )
        assert r_dept.status_code == 200, f"Dept update failed: {r_dept.text}"
        assert r_dept.json()["department"] == "Road Maintenance (PWD)"

        # Update status to in_progress
        r_prog = httpx.patch(
            f"{BACKEND_BASE}/api/complaints/{test_cid}/status",
            json={"status": "in_progress", "note": "Field crew arrived at Civil Lines."},
            headers={"X-Admin-Key": ADMIN_KEY},
            timeout=10
        )
        assert r_prog.status_code == 200, f"Status update to in_progress failed: {r_prog.text}"
        assert r_prog.json()["status"] == "in_progress"

        # Update status to resolved
        r_res = httpx.patch(
            f"{BACKEND_BASE}/api/complaints/{test_cid}/status",
            json={"status": "resolved", "note": "Pothole patched and leveled. Verification complete."},
            headers={"X-Admin-Key": ADMIN_KEY},
            timeout=10
        )
        assert r_res.status_code == 200, f"Status update to resolved failed: {r_res.text}"
        assert r_res.json()["status"] == "resolved"

        # Verify 4 history entries in database: submitted, reassigned, in_progress, resolved
        r_final = httpx.get(f"{BACKEND_BASE}/api/complaints/{test_cid}", timeout=10)
        hist = r_final.json()["history"]
        assert len(hist) == 4, f"Expected 4 history entries, got {len(hist)}"

        record("Workflow 8: Admin Status Updates & Department Reassignment", True, f"Updated status to 'in_progress' and 'resolved', reassigned department. 4 chronological history records verified.")
    except Exception as e:
        record("Workflow 8: Admin Status Updates & Department Reassignment", False, str(e))

    # 9. Security & Error Handling (Invalid images, missing fields, unauthorized admin)
    try:
        # Corrupt file
        r_bad_file = httpx.post(f"{BACKEND_BASE}/api/analyze", files={"file": ("fake.jpg", b"NOT_AN_IMAGE", "image/jpeg")}, timeout=10)
        assert r_bad_file.status_code == 400, f"Expected 400 for corrupt file, got {r_bad_file.status_code}"

        # Unauthorized admin status update (wrong key)
        r_unauth = httpx.patch(
            f"{BACKEND_BASE}/api/complaints/{test_cid}/status",
            json={"status": "resolved"},
            headers={"X-Admin-Key": "WRONG_SECRET_KEY"},
            timeout=10
        )
        assert r_unauth.status_code == 401, f"Expected 401 Unauthorized, got {r_unauth.status_code}"

        # Invalid status payload
        r_bad_status = httpx.patch(
            f"{BACKEND_BASE}/api/complaints/{test_cid}/status",
            json={"status": "INVALID_STATUS"},
            headers={"X-Admin-Key": ADMIN_KEY},
            timeout=10
        )
        assert r_bad_status.status_code == 400, f"Expected 400 Bad Request, got {r_bad_status.status_code}"

        # 404 for non-existent complaint
        r_404 = httpx.get(f"{BACKEND_BASE}/api/complaints/CF-2026-NONEXISTENT", timeout=10)
        assert r_404.status_code == 404, f"Expected 404 for non-existent, got {r_404.status_code}"

        record("Workflow 9: Security & Error Handling", True, "Corrupt file rejected (400), unauthorized admin rejected (401), invalid status rejected (400), unknown complaint returns 404.")
    except Exception as e:
        record("Workflow 9: Security & Error Handling", False, str(e))

    # 10. Data Persistence Check across server state
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT status FROM complaints WHERE complaint_id = ?", (test_cid,))
        s_db = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM status_history WHERE complaint_id = ?", (test_cid,))
        h_count = cur.fetchone()[0]
        con.close()
        assert s_db == "resolved", f"Expected resolved in DB, got {s_db}"
        assert h_count == 4, f"Expected 4 history rows, got {h_count}"

        record("Workflow 10: Persistent Storage Verification", True, f"Complaint {test_cid} and its 4 history rows verified in SQLite DB file.")
    except Exception as e:
        record("Workflow 10: Persistent Storage Verification", False, str(e))

    print("=" * 70)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"Summary: {passed_count}/{len(results)} workflows passed.")
    print("=" * 70)

if __name__ == "__main__":
    main()
