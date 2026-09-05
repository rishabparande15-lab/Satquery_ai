from pydantic import BaseModel, Field


class SearchQueryRequest(BaseModel):
    query: str | None = Field(default=None, description="Natural language search query")
    bbox: list[float] | None = Field(
        default=None,
        description="Bounding box [minLon, minLat, maxLon, maxLat] in WGS84",
    )
    start_date: str | None = Field(
        default=None, description="ISO start date filter (e.g. 2024-01-01)"
    )
    end_date: str | None = Field(
        default=None, description="ISO end date filter (e.g. 2024-12-31)"
    )
    mission: str = Field(
        default="Sentinel-2",
        description="Target mission platform (e.g. Sentinel-2)",
    )
    max_cloud_cover: float = Field(
        default=20.0,
        ge=0.0,
        le=100.0,
        description="Maximum allowed cloud coverage percentage",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of scenes to return",
    )


class ParsedQuery(BaseModel):
    bbox: list[float]
    datetime_range: str  # Format: "YYYY-MM-DD/YYYY-MM-DD"
    max_cloud_cover: float
    location_name: str
    mission: str
