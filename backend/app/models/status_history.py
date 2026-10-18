from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..db import Base

class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String(32), ForeignKey("complaints.complaint_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    note = Column(String(255), nullable=True)

    complaint = relationship("Complaint", back_populates="history")

    def to_dict(self):
        return {
            "id": self.id,
            "complaint_id": self.complaint_id,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "note": self.note
        }
