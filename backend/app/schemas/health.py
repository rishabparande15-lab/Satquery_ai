from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", description="Service health state")
    service: str = Field(default="satquery-ai-api", description="Service identifier")
    version: str = Field(default="0.1.0", description="API version")
    active_mode: str = Field(default="live", description="Active runtime mode: live or simulated")
    providers: list[str] = Field(
        default_factory=lambda: ["earth-search-stac"],
        description="Available external data providers",
    )
    capabilities: list[str] = Field(
        default_factory=lambda: [
            "sentinel-2-l2a-search",
            "bounded-window-ndvi",
            "remote-cog-streaming",
            "input-geospatial-validation",
            "pair-compatibility-check",
        ],
        description="Supported geospatial capabilities",
    )
    timestamp: str = Field(description="ISO timestamp of health check")
