from pydantic import BaseModel, Field


class NDVIAnalysisRequest(BaseModel):
    scene_id: str = Field(description="STAC Scene ID to analyze (e.g. Sentinel-2 L2A)")
    query: str | None = Field(default=None, description="Original user prompt or analysis intent")
    bbox: list[float] | None = Field(
        default=None,
        description="Optional sub-bounding box [minLon, minLat, maxLon, maxLat] within the scene",
    )
    window_pixels: int = Field(
        default=256,
        ge=64,
        le=1024,
        description="Window width/height in pixels for the bounded raster read",
    )


class VegetationDensityBreakdown(BaseModel):
    non_vegetated_or_water_percent: float = Field(
        description="NDVI < 0.1 (Water, bare soil, rock, urban impervious)"
    )
    sparse_vegetation_percent: float = Field(
        description="0.1 <= NDVI < 0.3 (Grasslands, sparse crops, arid scrub)"
    )
    moderate_vegetation_percent: float = Field(
        description="0.3 <= NDVI < 0.6 (Shrubland, developing crop canopy)"
    )
    dense_canopy_percent: float = Field(
        description="NDVI >= 0.6 (Dense forest canopy, vigorous crops)"
    )


class MetricDeltaItem(BaseModel):
    label: str
    value: str
    change: str | None = None  # None because single observation cannot provide delta
    trend: str = "stable"
    baseline: str
    unit: str


class NDVIAnalysisResponse(BaseModel):
    job_id: str
    scene_id: str
    mission: str = "Sentinel-2"
    query: str
    timestamp: str
    status: str = "completed"

    # Actual computed statistics
    valid_pixels: int
    total_pixels: int
    nodata_pixels: int
    area_analyzed_sq_km: float
    spatial_resolution_meters: float = 10.0

    min_ndvi: float | None = None
    max_ndvi: float | None = None
    mean_ndvi: float | None = None
    median_ndvi: float | None = None
    std_ndvi: float | None = None

    vegetation_density: VegetationDensityBreakdown
    source_assets: dict[str, str]

    # Scientific integrity: Explicitly unavailable fields for single pass
    confidence_score_percent: float | None = None  # null: single observation has no statistical confidence interval
    anomalies_detected_count: int | None = None   # null: requires multi-temporal baseline
    anomaly_notes: str = (
        "Multi-temporal anomaly baseline not implemented. Single scene NDVI provides biophysical status only."
    )

    metric_deltas: list[MetricDeltaItem] = Field(
        default_factory=list,
        description="Actual computed indicators without fabricated temporal changes",
    )

    executive_summary: str
    key_findings: list[str]
    methodology: str
    limitations: str
    processing_duration_ms: int
    is_real_analysis: bool = True
