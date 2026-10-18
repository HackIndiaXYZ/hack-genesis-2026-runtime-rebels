from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from ..db import Base

class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id = Column(String(32), primary_key=True, index=True)
    category = Column(String(64), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=0.85)
    severity = Column(String(32), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=False)
    department = Column(String(128), nullable=False)
    suggested_action = Column(String(255), nullable=True)
    complaint_text = Column(Text, nullable=False)
    language = Column(String(16), default="en")
    status = Column(String(32), nullable=False, default="submitted", index=True)
    duplicate_of = Column(String(32), nullable=True, index=True)
    estimated_resolution_hours = Column(Integer, default=48)
    image_path = Column(String(255), nullable=True)
    upvotes = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    history = relationship("StatusHistory", back_populates="complaint", cascade="all, delete-orphan", order_by="StatusHistory.timestamp.asc()")

    def to_dict(self):
        return {
            "complaint_id": self.complaint_id,
            "category": self.category,
            "confidence": round(self.confidence, 2),
            "severity": self.severity.lower(),
            "location": {
                "lat": self.latitude,
                "lng": self.longitude,
                "address": self.address
            },
            "department": self.department,
            "suggested_action": self.suggested_action,
            "complaint_text": self.complaint_text,
            "language": self.language,
            "status": self.status,
            "duplicate_of": self.duplicate_of,
            "estimated_resolution_hours": self.estimated_resolution_hours,
            "image_path": self.image_path,
            "upvotes": self.upvotes or 0,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "history": [h.to_dict() for h in self.history] if self.history else []
        }
