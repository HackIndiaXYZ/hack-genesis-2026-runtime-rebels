# CivicFix AI — Backend API

FastAPI backend providing intelligent civic complaint detection, municipal department routing, geospatial duplicate clustering, and automated resolution timeline tracking.

## 🚀 Quickstart

### 1. Setup Virtual Environment & Install Dependencies
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
Copy the example environment template:
```bash
cp .env.example .env
```
*(Optional: Provide `GEMINI_API_KEY` for Gemini-powered visual reasoning. If omitted, the system seamlessly operates using the local fallback detection and heuristic intelligence engine).*

### 3. Seed Database (Kanpur & Varanasi Dataset)
Populate the database with 22+ realistic civic complaints across Kanpur and Varanasi wards:
```bash
python seed.py
```

### 4. Start the Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📖 API Documentation
Once running, the interactive Swagger UI and schema documentation is available at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**
*(Alternative ReDoc interface available at `http://localhost:8000/redoc`)*

## 🛣️ API Endpoints Summary

| Endpoint | Method | Description |
| :--- | :---: | :--- |
| `/api/analyze` | `POST` | Multipart analysis of photo/video + GPS coordinates. Returns preview complaint draft and duplicate detection without saving yet. |
| `/api/complaints` | `POST` | Persists a confirmed complaint and initializes its chronological resolution timeline. |
| `/api/complaints` | `GET` | Lists civic complaints with filtering (`category`, `severity`, `status`) and pagination. |
| `/api/complaints/{id}` | `GET` | Fetches details and the complete event history timeline for a complaint. |
| `/api/complaints/{id}/status` | `PATCH` | Updates the status of an issue (`assigned`, `in_progress`, `resolved`, `rejected`) and appends to the history log. |
| `/api/complaints/{id}/upvote` | `POST` | Increments citizen upvote counter for duplicate issue escalation. |
| `/api/stats` | `GET` | Aggregated municipal KPIs, SLA resolution time, and category/severity/ward breakdown. |
| `/api/generate-complaint` | `POST` | Re-synthesizes formal complaint text for any updated location or language (8 Indian languages supported). |
| `/uploads/{filename}` | `GET` | Statically serves citizen-uploaded photographic evidence. |
| `/api/health` | `GET` | Backend health check and uptime probe. |
