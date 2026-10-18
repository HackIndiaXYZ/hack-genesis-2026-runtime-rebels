from typing import Optional, List
from pydantic import BaseModel, Field

class LocationSchema(BaseModel):
    lat: float
    lng: float
    address: str

class StatusHistorySchema(BaseModel):
    status: str
    timestamp: str
    note: Optional[str] = None

class ComplaintCreate(BaseModel):
    complaint_id: Optional[str] = None
    category: str
    confidence: Optional[float] = 0.90
    severity: str
    location: LocationSchema
    department: Optional[str] = None
    suggested_action: Optional[str] = None
    complaint_text: str
    language: Optional[str] = "en"
    status: Optional[str] = "submitted"
    duplicate_of: Optional[str] = None
    estimated_resolution_hours: Optional[int] = 48
    image_path: Optional[str] = None

class StatusUpdateSchema(BaseModel):
    status: str
    note: Optional[str] = None
    department: Optional[str] = None

class DepartmentAssignSchema(BaseModel):
    department: str
    note: Optional[str] = None

class ComplaintResponse(BaseModel):
    complaint_id: str
    category: str
    confidence: float
    severity: str
    location: LocationSchema
    department: str
    suggested_action: Optional[str] = None
    complaint_text: str
    language: Optional[str] = "en"
    status: str
    duplicate_of: Optional[str] = None
    estimated_resolution_hours: int
    image_path: Optional[str] = None
    upvotes: int = 0
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    history: List[StatusHistorySchema] = []
