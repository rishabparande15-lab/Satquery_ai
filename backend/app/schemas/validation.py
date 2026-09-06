from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

ValidationStatus = Literal["passed", "warning", "failed"]


class ValidationCheck(BaseModel):
    id: str
    label: str
    status: ValidationStatus
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class GeospatialMetadata(BaseModel):
    crs: str | None = None
    epsg: int | None = None
    is_projected: bool | None = None
    bounds: list[float] | None = None  # [min_lon, min_lat, max_lon, max_lat]
    dimensions: dict[str, int] | None = None  # e.g. {"width": int, "height": int}
    band_count: int | None = None
    spatial_resolution_meters: float | None = None
    acquisition_date: str | None = None
    nodata_value: float | int | str | None = None
    declared_format: str | None = None


class ImageQualityReport(BaseModel):
    cloud_cover_percent: float | None = None
    valid_pixel_ratio: float | None = None
    quality_assessment: str = "unverified"
    details: dict[str, Any] = Field(default_factory=dict)


class InputValidationResponse(BaseModel):
    scene_id: str
    overall_status: ValidationStatus
    modality: str
    ndvi_ready: bool
    metadata: GeospatialMetadata = Field(default_factory=GeospatialMetadata)
    quality: ImageQualityReport = Field(default_factory=ImageQualityReport)
    checks: list[ValidationCheck]
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    validated_at: datetime


class ScenePairValidationRequest(BaseModel):
    before_scene_id: str
    after_scene_id: str


class ScenePairValidationResponse(BaseModel):
    before_scene_id: str
    after_scene_id: str
    overall_status: ValidationStatus
    temporal_order_valid: bool | None = None
    overlap_percent_estimate: float | None = None
    crs_compatible: bool
    resolution_compatible: bool | None = None
    coregistration_assessment: str
    checks: list[ValidationCheck]
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    validated_at: datetime
