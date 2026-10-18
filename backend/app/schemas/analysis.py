from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from .complaint import LocationSchema

class DetectionItem(BaseModel):
    category: str
    confidence: float
    box: Optional[List[float]] = None
    severity: Optional[float] = None
    severity_label: Optional[str] = None

class AnalyzeResponse(BaseModel):
    complaint_id: str
    category: str
    confidence: float
    severity: str
    location: LocationSchema
    department: str
    suggested_action: str
    complaint_text: str
    language: str = "en"
    duplicate_of: Optional[str] = None
    duplicate_count: Optional[int] = 0
    estimated_resolution_hours: int
    image_path: Optional[str] = None
    detections: Optional[List[Dict[str, Any]]] = []
    vlm_description: Optional[str] = None
    needs_review: bool = False
    review_reason: Optional[str] = None
    consensus_mode: Optional[str] = None
    raw_yolo: Optional[Dict[str, Any]] = None
    raw_vlm: Optional[Dict[str, Any]] = None

class GenerateComplaintRequest(BaseModel):
    category: str
    severity: str
    address: str
    language: Optional[str] = "en"

class GenerateComplaintResponse(BaseModel):
    complaint_text: str
