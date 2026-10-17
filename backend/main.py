import sys, json, uuid, shutil, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT))
from vision import analyze_image
import intelligence

HERE = Path(__file__).parent
UPLOADS = HERE / "uploads"
UPLOADS.mkdir(exist_ok=True)
DB_PATH = HERE / "civicfix.db"

app = FastAPI(title="CivicFix AI")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=UPLOADS), name="uploads")

STATUSES = ["submitted", "verified", "assigned", "in progress", "resolved"]

# model class (substring) -> (frontend category, department, suggested action)
ISSUES = {
    "pothole": ("pothole", "Road Maintenance", "Immediate repair required"),
    "manhole": ("open manhole", "Public Works", "Immediate barricading and cover replacement"),
    "garbage": ("overflowing garbage", "Sanitation", "Schedule pickup within 24 hours"),
    "streetlight": ("broken streetlight", "Electrical", "Inspect and replace bulb"),
    "road_sign": ("damaged road sign", "Traffic Police", "Replace or repair the sign"),
    "water_leak": ("water leakage", "Water Supply", "Dispatch plumber to inspect pipeline"),
}

# ---------- database ----------
def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

_c = db()
_c.execute("CREATE TABLE IF NOT EXISTS complaints (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT NOT NULL)")
_c.commit()
_c.close()

def row_id(cid):
    digits = "".join(ch for ch in str(cid) if ch.isdigit())
    return int(digits) if digits else None

def save_new(complaint):
    conn = db()
    try:
        cur = conn.execute("INSERT INTO complaints (data) VALUES (?)", ("{}",))
        complaint["complaint_id"] = f"CF-{cur.lastrowid:04d}"
        conn.execute("UPDATE complaints SET data=? WHERE id=?", (json.dumps(complaint), cur.lastrowid))
        conn.commit()
    finally:
        conn.close()
    return complaint

def load(cid):
    conn = db()
    try:
        row = conn.execute("SELECT data FROM complaints WHERE id=?", (row_id(cid),)).fetchone()
    finally:
        conn.close()
    return json.loads(row["data"]) if row else None

def store(cid, complaint):
    conn = db()
    try:
        conn.execute("UPDATE complaints SET data=? WHERE id=?", (json.dumps(complaint), row_id(cid)))
        conn.commit()
    finally:
        conn.close()

# ---------- helpers ----------
def to_plain(obj):
    return json.loads(json.dumps(obj, default=lambda o: o.item() if hasattr(o, "item") else str(o)))

def field(form, *names):
    for n in names:
        v = form.get(n)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None

def to_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None

def text_from(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for k in ("complaint_text", "text", "complaint", "description"):
            if isinstance(value.get(k), str):
                return value[k]
    return None

# ---------- routes ----------
@app.get("/api/complaints")
def list_complaints():
    conn = db()
    try:
        rows = conn.execute("SELECT data FROM complaints ORDER BY id DESC").fetchall()
    finally:
        conn.close()
    return [json.loads(r["data"]) for r in rows]

@app.get("/api/complaints/{cid}")
def get_complaint(cid: str):
    c = load(cid)
    if not c:
        raise HTTPException(404, "Complaint not found")
    return c

@app.patch("/api/complaints/{cid}/status")
async def update_status(cid: str, request: Request):
    body = await request.json()
    status = str(body.get("status", "")).lower()
    if status not in STATUSES:
        raise HTTPException(400, f"status must be one of {STATUSES}")
    c = load(cid)
    if not c:
        raise HTTPException(404, "Complaint not found")
    c["status"] = status
    store(cid, c)
    return c

@app.post("/api/analyze")
async def analyze(request: Request):
    form = await request.form()
    print("form fields:", list(form.keys()))
    upload = next((v for v in form.values() if hasattr(v, "filename")), None)
    if upload is None:
        raise HTTPException(400, "No image in form data")

    path = UPLOADS / f"{uuid.uuid4().hex}_{Path(upload.filename).name}"
    with open(path, "wb") as f:
        shutil.copyfileobj(upload.file, f)

    result = to_plain(analyze_image(str(path)))
    print("analyze_image result:", result)
    detections = result.get("detections") or []
    if not detections:
        return {"found": False, "message": "No civic issue detected", "image_url": f"/uploads/{path.name}"}

    best = max(detections, key=lambda d: to_float(d.get("confidence") or d.get("conf")) or 0)
    raw = str(best.get("category") or best.get("label") or best.get("class")
              or best.get("name") or result.get("category") or "unknown")
    confidence = to_float(best.get("confidence") or best.get("conf")) or 0.0
    severity = str(best.get("severity_label") or "").lower()
    if severity not in ("low", "medium", "high", "critical"):
        sv = to_float(best.get("severity"))
        severity = "high" if (sv or 0) >= 0.66 else "medium" if (sv or 0) >= 0.33 else "low"

    key = raw.lower().replace(" ", "_").replace("-", "_")
    category, department, action = next(
        (v for k, v in ISSUES.items() if k in key),
        (raw, "Municipal Corporation", "Inspect and resolve"),
    )

    lat = to_float(field(form, "lat", "latitude"))
    lng = to_float(field(form, "lng", "lon", "longitude"))
    accuracy = to_float(field(form, "accuracy"))
    address = field(form, "address") or "Unknown location"
    language = field(form, "language", "lang") or "en"

    generated = None
    try:
        generated = text_from(intelligence.generate_complaint(key, severity, address, language))
    except Exception as e:
        print("generate_complaint failed:", e)
    text = (field(form, "complaint_text", "description") or generated
            or f"{category.capitalize()} reported at {address}. Severity: {severity}.")

    hours = 48
    try:
        days = intelligence.predict_resolution_days(key, severity, department)
        days = days.get("days") if isinstance(days, dict) else days
        hours = int(float(days) * 24)
    except Exception as e:
        print("predict_resolution_days failed:", e)

    complaint = {
        "found": True,
        "category": category,
        "confidence": round(confidence, 3),
        "severity": severity,
        "location": {"lat": lat, "lng": lng, "address": address, "accuracy": accuracy},
        "department": department,
        "suggested_action": action,
        "complaint_text": text,
        "status": "submitted",
        "duplicate_of": None,
        "estimated_resolution_hours": hours,
        "image_url": f"/uploads/{path.name}",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "detections": detections,
    }
    return save_new(complaint)