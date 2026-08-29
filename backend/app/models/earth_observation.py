from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class EarthObservation(Base):
    """
    Earth Observation satellite acquisition metadata record.
    Represents catalogued remote sensing scenes (SAR, Optical DEM, NISAR)
    retrieved from Bhoonidhi / NRSC open data portal.
    NOTE: Stores structured metadata and scene availability only.
    Raw multi-gigabyte satellite binaries are not stored directly in relational tables.
    """
    __tablename__ = "earth_observations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    location_id = Column(String(50), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    collection = Column(String(100), nullable=False, index=True)  # e.g. Sentinel-1A_SAR-IW_GRD, CartoSat-1_PAN_CartoDEM_30m
    product_id = Column(String(150), nullable=False, unique=True, index=True)  # Granule identifier

    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    acquisition_start = Column(DateTime(timezone=True), nullable=True)
    acquisition_end = Column(DateTime(timezone=True), nullable=True)

    platform = Column(String(50), nullable=False)  # Sentinel-1A, CartoSat-1, NISAR
    instrument = Column(String(50), nullable=False)  # C-SAR, PAN, L-SAR
    processing_level = Column(String(50), default="Level-1 GRD")  # Level-1 GRD, Level-3 DEM, Level-2 GCOV

    bbox_json = Column(JSON, nullable=True)  # [min_lon, min_lat, max_lon, max_lat]
    geometry_json = Column(JSON, nullable=True)  # GeoJSON polygon

    available_online = Column(Boolean, default=True)
    source = Column(String(50), default="BHOONIDHI_ISRO")  # BHOONIDHI_ISRO, MOCK_STAC
    metadata_json = Column(JSON, nullable=True)  # Orbit, polarization, resolution, download_url
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Optional relationship
    location = relationship("Location", lazy="selectin")

    __table_args__ = (
        Index("ix_earth_obs_coll_time", "collection", "timestamp"),
    )
