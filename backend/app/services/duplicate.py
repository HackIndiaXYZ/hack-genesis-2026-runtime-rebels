import math
from difflib import SequenceMatcher
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from ..models.complaint import Complaint

# Try optional sentence-transformers
_st_model = None
try:
    from sentence_transformers import SentenceTransformer, util
    # Lazy loaded when first needed to save startup memory
except Exception:
    _st_model = None

def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in meters."""
    earth_radius_m = 6_371_000.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2.0) ** 2)
    return earth_radius_m * 2.0 * math.asin(min(1.0, math.sqrt(a)))

def compute_similarity(text1: str, text2: str) -> float:
    """Computes similarity using Sentence Transformers if loaded, else SequenceMatcher."""
    global _st_model
    t1 = (text1 or "").strip().lower()
    t2 = (text2 or "").strip().lower()
    if not t1 or not t2:
        return 0.0

    if _st_model is not None:
        try:
            emb1 = _st_model.encode(t1, convert_to_tensor=True)
            emb2 = _st_model.encode(t2, convert_to_tensor=True)
            score = float(util.cos_sim(emb1, emb2)[0][0])
            return max(0.0, min(1.0, score))
        except Exception:
            pass

    return SequenceMatcher(None, t1, t2).ratio()

def find_duplicate_complaint(
    db: Session,
    category: str,
    lat: float,
    lng: float,
    text: str,
    radius_m: float = 50.0,
    similarity_threshold: float = 0.65
) -> Optional[Complaint]:
    """
    Checks for an existing active complaint with the same category within 50m radius
    and high text similarity.
    """
    if lat is None or lng is None:
        return None

    # Filter by same category and active status
    candidates = db.query(Complaint).filter(
        Complaint.category == category,
        Complaint.status.in_(["submitted", "assigned", "in_progress"])
    ).all()

    best_match = None
    best_score = -1.0

    for cand in candidates:
        dist = haversine_m(lat, lng, cand.latitude, cand.longitude)
        if dist > radius_m:
            continue

        sim = compute_similarity(text, cand.complaint_text)
        dist_score = 1.0 - (dist / radius_m)
        comb = 0.6 * dist_score + 0.4 * sim

        # Flag as duplicate if within 25m of identical category, or combined score meets threshold
        if (dist <= 25.0) or (comb >= 0.50) or (sim >= similarity_threshold):
            if comb > best_score:
                best_score = comb
                best_match = cand

    return best_match
