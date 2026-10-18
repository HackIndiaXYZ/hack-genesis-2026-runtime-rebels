import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..db import get_db
from ..models.complaint import Complaint
from ..schemas.stats import StatsResponse

router = APIRouter(prefix="/api/stats", tags=["Analytics & KPIs"])

@router.get("", response_model=StatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Computes aggregated KPIs and breakdowns for the Landing page and Admin dashboard:
    - Total complaints
    - Resolved complaints
    - Critical issues
    - Average resolution time
    - Grouped counts by category, severity, and ward/locality
    """
    all_complaints = db.query(Complaint).all()
    total = len(all_complaints)
    resolved = sum(1 for c in all_complaints if c.status == "resolved")
    critical = sum(1 for c in all_complaints if c.severity == "critical")
    in_progress = sum(1 for c in all_complaints if c.status == "in_progress")
    submitted = sum(1 for c in all_complaints if c.status == "submitted")

    total_hours = sum(c.estimated_resolution_hours or 48 for c in all_complaints)
    avg_hours = round(total_hours / total) if total > 0 else 42

    by_category = {}
    by_severity = {}
    by_ward = {}

    for c in all_complaints:
        cat = c.category.lower().strip()
        by_category[cat] = by_category.get(cat, 0) + 1

        sev = c.severity.lower().strip()
        by_severity[sev] = by_severity.get(sev, 0) + 1

        # Extract Ward or locality if present in address
        ward_match = re.search(r"Ward\s*(\d+)", c.address or "", re.IGNORECASE)
        if ward_match:
            ward_name = f"Ward {ward_match.group(1)}"
        else:
            # Fallback to first locality token
            parts = (c.address or "").split(",")
            ward_name = parts[0].strip() if parts else "Central Ward"
        
        by_ward[ward_name] = by_ward.get(ward_name, 0) + 1

    return StatsResponse(
        total=total,
        resolved=resolved,
        critical=critical,
        in_progress=in_progress,
        submitted=submitted,
        avg_resolution_hours=avg_hours,
        by_category=by_category,
        by_severity=by_severity,
        by_ward=by_ward
    )
