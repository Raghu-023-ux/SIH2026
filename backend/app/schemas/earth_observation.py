from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EarthObservationSearchRequest(BaseModel):
    collection: Optional[str] = Field(
        default=None,
        description="Collection name e.g. Sentinel-1A_SAR-IW_GRD, CartoSat-1_PAN_CartoDEM_30m, NISAR_SSAR_GCOV"
    )
    location_id: Optional[str] = Field(default=None, description="Monitored station identifier")
    bbox: Optional[List[float]] = Field(default=None, description="Bounding box: [min_lon, min_lat, max_lon, max_lat]")
    start_date: Optional[datetime] = Field(default=None, description="Acquisition start window (UTC)")
    end_date: Optional[datetime] = Field(default=None, description="Acquisition end window (UTC)")
    limit: int = Field(default=10, ge=1, le=50, description="Max metadata records to return")


class EarthObservationItemResponse(BaseModel):
    id: str
    location_id: Optional[str] = None
    collection: str
    product_id: str
    timestamp: datetime
    acquisition_start: Optional[datetime] = None
    acquisition_end: Optional[datetime] = None
    platform: str
    instrument: str
    processing_level: str
    bbox: Optional[List[float]] = None
    available_online: bool = True
    source: str = "BHOONIDHI_ISRO"
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EarthObservationSearchResponse(BaseModel):
    total_results: int
    provider: str
    provider_status: str  # AVAILABLE, NOT_CONFIGURED, RATE_LIMITED, MOCK_MODE
    cached: bool = False
    results: List[EarthObservationItemResponse] = Field(default_factory=list)


class BhoonidhiStatusResponse(BaseModel):
    provider_name: str = "Bhoonidhi (ISRO / NRSC Open Data Portal)"
    status: str  # AVAILABLE, NOT_CONFIGURED, RATE_LIMITED, MOCK_MODE
    configured: bool = False
    api_endpoint: str
    token_valid: bool = False
    supported_collections: List[str] = Field(default_factory=list)
    rate_limits: Dict[str, Any] = Field(default_factory=dict)
    latest_synced_scene: Optional[str] = None
    note: str
