import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .db import engine, Base
from .routers import complaints_router, analysis_router, stats_router
from .services.file_service import UPLOAD_DIR

# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CivicFix AI API",
    description="Intelligent Municipal Civic Complaint Detection, Assessment, and Routing Platform",
    version="2.0.0"
)

# Configure CORS - separate production from dev
is_production = os.getenv("ENVIRONMENT") == "production"

if is_production:
    allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    origin_regex = None  # Strict origin whitelist in production; no localhost regex
else:
    allowed_origins_env = os.getenv(
        "ALLOWED_ORIGINS", 
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174,http://localhost:3000"
    )
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
    origin_regex = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded static assets
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Include API Routers
app.include_router(complaints_router)
app.include_router(analysis_router)
app.include_router(stats_router)

@app.get("/")
def root():
    return {
        "service": "CivicFix AI API",
        "status": "online",
        "documentation": "/docs",
        "health": "/api/health",
        "endpoints": {
            "complaints": "/api/complaints",
            "analyze": "/api/analyze",
            "stats": "/api/stats"
        }
    }

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CivicFix AI Backend",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=True)
