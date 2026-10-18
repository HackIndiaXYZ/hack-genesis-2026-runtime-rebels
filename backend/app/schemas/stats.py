from typing import Dict
from pydantic import BaseModel

class StatsResponse(BaseModel):
    total: int
    resolved: int
    critical: int
    in_progress: int
    submitted: int
    avg_resolution_hours: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
    by_ward: Dict[str, int]
