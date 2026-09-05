from pydantic import BaseModel, Field


class SpectralBand(BaseModel):
    id: str
    name: str
    commonName: str
    centralWavelengthMicrons: float
    bandwidthMicrons: float
    spatialResolutionMeters: int
    description: str
    domain: str


class CenterCoordinates(BaseModel):
    lat: float
    lon: float


class SceneResponse(BaseModel):
    id: str
    title: str
    mission: str = "Sentinel-2"
    sensor: str = "Multispectral"
    platformId: str
    instrument: str = "MSI (MultiSpectral Instrument)"
    acquisitionDate: str
    cloudCoverPercent: float
    spatialResolutionMeters: int = 10
    crs: str
    sunElevationDeg: float
    sunAzimuthDeg: float
    processingLevel: str = "Level-2A (Bottom of Atmosphere Surface Reflectance)"
    centerCoordinates: CenterCoordinates
    boundingBox: list[float]  # [minLon, minLat, maxLon, maxLat]
    locationName: str
    orbitPass: str = "Descending"
    relativeOrbitNumber: int = 0
    bands: list[SpectralBand]
    simulatedLayerColorMap: dict[str, str] = Field(
        default_factory=lambda: {
            "true_color": "#1a3c40",
            "false_color_ir": "#b83b5e",
            "ndvi": "#2dc653",
            "sar_amplitude": "#6c757d",
            "thermal": "#d97706",
        }
    )
    thumbnailSvgType: str = "urban_port"
    stacSelfHref: str
    dataSizeMb: float = 650.0
    isRealData: bool = True
    previewUrl: str | None = None


class SceneDetailResponse(SceneResponse):
    assets: dict[str, dict[str, str | None]] = Field(
        default_factory=dict, description="Resolved STAC assets dictionary"
    )
    stac_item_json: dict | None = None
