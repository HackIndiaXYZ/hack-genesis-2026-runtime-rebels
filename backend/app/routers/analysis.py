from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..schemas.analysis import AnalyzeResponse, GenerateComplaintRequest, GenerateComplaintResponse
from ..services.file_service import save_upload_file, UPLOAD_DIR
from ..services.ai_pipeline import run_ai_pipeline, generate_complaint_text
from ..services.duplicate import find_duplicate_complaint

router = APIRouter(prefix="/api", tags=["Analysis & AI"])

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_issue(
    file: UploadFile = File(...),
    latitude: float = Form(25.3176),
    longitude: float = Form(82.9739),
    address: str = Form("Civil Lines, Kanpur"),
    language: str = Form("en"),
    db: Session = Depends(get_db)
):
    """
    Analyzes an uploaded photo/video using the AI pipeline:
    - Object Detection & Severity
    - VLM Verification
    - Multilingual Complaint Synthesis
    - Geospatial & Semantic Duplicate Detection
    Does NOT save to database yet (returns preview draft).
    """
    # 1. Save uploaded file securely
    rel_path = await save_upload_file(file)
    abs_path = str(UPLOAD_DIR / rel_path.split("/")[-1])

    # 2. Run AI Pipeline
    pipeline_res = await run_ai_pipeline(
        image_abs_path=abs_path,
        lat=latitude,
        lng=longitude,
        address=address,
        language=language
    )

    # 3. Check for duplicates in DB
    dup = find_duplicate_complaint(
        db=db,
        category=pipeline_res["category"],
        lat=latitude,
        lng=longitude,
        text=pipeline_res["complaint_text"],
        radius_m=50.0
    )

    duplicate_of = dup.complaint_id if dup else None
    duplicate_count = dup.upvotes if dup else 0

    return AnalyzeResponse(
        complaint_id=pipeline_res["complaint_id"],
        category=pipeline_res["category"],
        confidence=pipeline_res["confidence"],
        severity=pipeline_res["severity"],
        location={
            "lat": latitude,
            "lng": longitude,
            "address": address
        },
        department=pipeline_res["department"],
        suggested_action=pipeline_res["suggested_action"],
        complaint_text=pipeline_res["complaint_text"],
        language=language,
        duplicate_of=duplicate_of,
        duplicate_count=duplicate_count,
        estimated_resolution_hours=pipeline_res["estimated_resolution_hours"],
        image_path=rel_path,
        vlm_description=pipeline_res.get("vlm_description"),
        needs_review=pipeline_res.get("needs_review", False),
        review_reason=pipeline_res.get("review_reason"),
        consensus_mode=pipeline_res.get("consensus_mode"),
        raw_yolo=pipeline_res.get("raw_yolo"),
        raw_vlm=pipeline_res.get("raw_vlm")
    )

@router.post("/generate-complaint", response_model=GenerateComplaintResponse)
def regenerate_complaint_text(payload: GenerateComplaintRequest):
    """Regenerates a formal complaint text for an updated location, severity, or language."""
    text = generate_complaint_text(
        category=payload.category,
        severity=payload.severity,
        address=payload.address,
        language=payload.language or "en"
    )
    return GenerateComplaintResponse(complaint_text=text)
