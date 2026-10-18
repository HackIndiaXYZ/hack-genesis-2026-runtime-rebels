import os
import random
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..db import get_db
from ..models.complaint import Complaint
from ..models.status_history import StatusHistory
from ..schemas.complaint import (
    ComplaintCreate,
    ComplaintResponse,
    StatusUpdateSchema,
    DepartmentAssignSchema
)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

def verify_admin_access(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None)
) -> bool:
    """
    Enforces authorization for privileged administrative endpoints.
    In production (ENVIRONMENT=production), ADMIN_API_KEY is strictly mandatory.
    Supports either 'X-Admin-Key' header or 'Authorization: Bearer <key>'.
    """
    required_key = (os.getenv("ADMIN_API_KEY") or "").strip()
    is_production = os.getenv("ENVIRONMENT") == "production"

    if is_production and not required_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security configuration error: ADMIN_API_KEY must be configured in production."
        )

    if not required_key:
        return True  # Dev mode default when no secret configured outside production

    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    provided_key = (x_admin_key or token or "").strip()

    if provided_key != required_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid admin authorization key."
        )
    return True

def generate_complaint_id() -> str:
    return f"CF-2026-{random.randint(10000, 99999)}"

@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    """
    Persists a confirmed complaint to the database and initializes its status timeline.
    """
    cid = payload.complaint_id or generate_complaint_id()

    # Ensure unique complaint_id
    while db.query(Complaint).filter(Complaint.complaint_id == cid).first():
        cid = generate_complaint_id()

    complaint = Complaint(
        complaint_id=cid,
        category=payload.category,
        confidence=payload.confidence or 0.88,
        severity=payload.severity.lower(),
        latitude=payload.location.lat,
        longitude=payload.location.lng,
        address=payload.location.address,
        department=payload.department or "Municipal Public Works",
        suggested_action=payload.suggested_action,
        complaint_text=payload.complaint_text,
        language=payload.language or "en",
        status=payload.status or "submitted",
        duplicate_of=payload.duplicate_of,
        estimated_resolution_hours=payload.estimated_resolution_hours or 48,
        image_path=payload.image_path,
        upvotes=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    db.add(complaint)
    db.flush()

    # Create initial status history entry
    first_history = StatusHistory(
        complaint_id=cid,
        status=complaint.status,
        timestamp=datetime.now(timezone.utc),
        note="Complaint submitted and verified by citizen."
    )
    db.add(first_history)
    db.commit()
    db.refresh(complaint)

    return complaint.to_dict()

@router.get("", response_model=List[ComplaintResponse])
def list_complaints(
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Lists active and past complaints with optional filtering by category, severity, and status.
    """
    query = db.query(Complaint)

    if category:
        query = query.filter(Complaint.category.ilike(f"%{category}%"))
    if severity:
        query = query.filter(Complaint.severity == severity.lower())
    if status:
        query = query.filter(Complaint.status == status.lower())

    results = query.order_by(desc(Complaint.created_at)).offset(offset).limit(limit).all()
    return [c.to_dict() for c in results]

@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint_details(complaint_id: str, db: Session = Depends(get_db)):
    """
    Returns full details for a specific complaint along with its chronological status timeline.
    """
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found.")
    return complaint.to_dict()

@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_complaint_status(
    complaint_id: str,
    payload: StatusUpdateSchema,
    _auth: bool = Depends(verify_admin_access),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to update the status of an issue (e.g. assigned, in_progress, resolved, rejected)
    and optionally reassign department, automatically logging an entry in the status timeline.
    Protected by ADMIN_API_KEY when set in environment.
    """
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found.")

    new_status = payload.status.lower()
    valid_statuses = {"submitted", "assigned", "in_progress", "resolved", "rejected"}
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Allowed: {', '.join(sorted(valid_statuses))}"
        )

    complaint.status = new_status
    if payload.department:
        complaint.department = payload.department.strip()
    complaint.updated_at = datetime.now(timezone.utc)

    # Append to status history
    history_entry = StatusHistory(
        complaint_id=complaint_id,
        status=new_status,
        timestamp=datetime.now(timezone.utc),
        note=payload.note or f"Status changed to {new_status.replace('_', ' ').capitalize()}."
    )
    db.add(history_entry)
    db.commit()
    db.refresh(complaint)

    return complaint.to_dict()

@router.patch("/{complaint_id}/department", response_model=ComplaintResponse)
def assign_department(
    complaint_id: str,
    payload: DepartmentAssignSchema,
    _auth: bool = Depends(verify_admin_access),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint to reassign a complaint to a specific municipal department.
    Protected by ADMIN_API_KEY when set in environment.
    """
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found.")

    complaint.department = payload.department.strip()
    complaint.updated_at = datetime.now(timezone.utc)

    history_entry = StatusHistory(
        complaint_id=complaint_id,
        status=complaint.status,
        timestamp=datetime.now(timezone.utc),
        note=payload.note or f"Reassigned to {payload.department.strip()}."
    )
    db.add(history_entry)
    db.commit()
    db.refresh(complaint)

    return complaint.to_dict()

@router.post("/{complaint_id}/upvote")
def upvote_complaint(complaint_id: str, db: Session = Depends(get_db)):
    """
    Increments the upvote count of a complaint when citizens report a duplicate.
    """
    complaint = db.query(Complaint).filter(Complaint.complaint_id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint '{complaint_id}' not found.")

    complaint.upvotes = (complaint.upvotes or 0) + 1
    db.commit()
    return {"complaint_id": complaint_id, "upvotes": complaint.upvotes}
