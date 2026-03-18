from pydantic import BaseModel
from typing import List, Optional

class Zone(BaseModel):
    zone_id: int
    health_score: float
    severity: str        # "HIGH" | "MODERATE" | "LOW"
    area: float
    issue: str
    recommendation: str

class Summary(BaseModel):
    healthy: float
    moderate: float
    severe: float
    total_zones: int

class GeoRef(BaseModel):
    lat: Optional[float] = None
    lon: Optional[float] = None
    status: str = "unavailable"

class AnalyzeResponse(BaseModel):
    status: str
    map: str  # base64_image
    geo: GeoRef
    summary: Summary
    zones: List[Zone]
