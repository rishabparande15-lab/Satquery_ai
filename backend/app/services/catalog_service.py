import logging
from typing import Any
from ..providers.stac_provider import stac_provider
from ..schemas.query import ParsedQuery
from ..schemas.scene import SceneResponse, SpectralBand, CenterCoordinates

logger = logging.getLogger(__name__)

# Standard Sentinel-2 MSI Spectral Band Definitions
SENTINEL_2_BANDS: list[SpectralBand] = [
    SpectralBand(
        id="B01",
        name="Coastal Aerosol",
        commonName="coastal",
        centralWavelengthMicrons=0.443,
        bandwidthMicrons=0.02,
        spatialResolutionMeters=60,
        description="Coastal aerosol retrieval and atmospheric correction.",
        domain="Visible",
    ),
    SpectralBand(
        id="B02",
        name="Blue",
        commonName="blue",
        centralWavelengthMicrons=0.490,
        bandwidthMicrons=0.065,
        spatialResolutionMeters=10,
        description="Visible blue band for bathymetry and soil differentiation.",
        domain="Visible",
    ),
    SpectralBand(
        id="B03",
        name="Green",
        commonName="green",
        centralWavelengthMicrons=0.560,
        bandwidthMicrons=0.035,
        spatialResolutionMeters=10,
        description="Chlorophyll peak reflectance for vegetation discrimination.",
        domain="Visible",
    ),
    SpectralBand(
        id="B04",
        name="Red",
        commonName="red",
        centralWavelengthMicrons=0.665,
        bandwidthMicrons=0.030,
        spatialResolutionMeters=10,
        description="Chlorophyll absorption band, critical for NDVI index.",
        domain="Visible",
    ),
    SpectralBand(
        id="B05",
        name="Vegetation Red Edge 1",
        commonName="rededge1",
        centralWavelengthMicrons=0.705,
        bandwidthMicrons=0.015,
        spatialResolutionMeters=20,
        description="Onset of red edge slope, sensitive to leaf nitrogen.",
        domain="Red-Edge",
    ),
    SpectralBand(
        id="B06",
        name="Vegetation Red Edge 2",
        commonName="rededge2",
        centralWavelengthMicrons=0.740,
        bandwidthMicrons=0.015,
        spatialResolutionMeters=20,
        description="Red edge transition zone for leaf area index (LAI).",
        domain="Red-Edge",
    ),
    SpectralBand(
        id="B07",
        name="Vegetation Red Edge 3",
        commonName="rededge3",
        centralWavelengthMicrons=0.783,
        bandwidthMicrons=0.020,
        spatialResolutionMeters=20,
        description="Upper boundary of red edge plateau.",
        domain="Red-Edge",
    ),
    SpectralBand(
        id="B08",
        name="Broad Near-Infrared (NIR)",
        commonName="nir",
        centralWavelengthMicrons=0.842,
        bandwidthMicrons=0.115,
        spatialResolutionMeters=10,
        description="High reflectance over dense biomass and cellular structure.",
        domain="Near-Infrared",
    ),
    SpectralBand(
        id="B8A",
        name="Narrow NIR",
        commonName="nir08",
        centralWavelengthMicrons=0.865,
        bandwidthMicrons=0.020,
        spatialResolutionMeters=20,
        description="Water vapor avoidance narrow band.",
        domain="Near-Infrared",
    ),
    SpectralBand(
        id="B11",
        name="SWIR 1",
        commonName="swir16",
        centralWavelengthMicrons=1.610,
        bandwidthMicrons=0.090,
        spatialResolutionMeters=20,
        description="Canopy moisture content and snow/cloud separation.",
        domain="Shortwave-Infrared",
    ),
    SpectralBand(
        id="B12",
        name="SWIR 2",
        commonName="swir22",
        centralWavelengthMicrons=2.190,
        bandwidthMicrons=0.180,
        spatialResolutionMeters=20,
        description="Hydrothermal alteration and burned area mapping.",
        domain="Shortwave-Infrared",
    ),
]


class CatalogService:
    """Orchestrates STAC search and transforms STAC GeoJSON into frontend-ready SceneResponse objects."""

    def transform_stac_feature(self, feature: dict[str, Any], location_name: str) -> SceneResponse:
        props = feature.get("properties", {})
        item_id = feature.get("id", "S2_UNKNOWN")
        bbox = feature.get("bbox", [0.0, 0.0, 0.0, 0.0])

        # Center coordinates
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0

        # Acquisition time
        dt = props.get("datetime") or props.get("created") or "2024-01-01T00:00:00Z"

        # Cloud cover
        cloud_val = props.get("eo:cloud_cover")
        if cloud_val is None:
            cloud_val = props.get("s2:high_proba_clouds_percentage", 0.0)
        cloud_percent = float(cloud_val)

        # Platform
        platform = props.get("platform", "Sentinel-2").upper()
        if "SENTINEL-2" not in platform:
            platform = f"SENTINEL-2 ({platform})"

        # Projection / CRS
        epsg = props.get("proj:epsg")
        crs_str = f"EPSG:{epsg} (WGS 84 / UTM)" if epsg else "EPSG:4326 (WGS 84)"

        # Sun angles
        sun_elev = float(props.get("view:sun_elevation", 55.0))
        sun_azimuth = float(props.get("view:sun_azimuth", 145.0))

        # Self link / STAC URI
        links = feature.get("links", [])
        self_href = next((l["href"] for l in links if l.get("rel") == "self"), "")
        if not self_href:
            self_href = f"https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/{item_id}"

        # Relative orbit
        rel_orbit = int(props.get("sat:relative_orbit", 0))

        # Assets & Thumbnail
        assets = feature.get("assets", {})
        thumbnail_url = None
        for key in ["thumbnail", "overview", "rendered_preview"]:
            if key in assets:
                thumbnail_url = assets[key].get("href")
                break

        title = f"{platform} MSI L2A: {location_name}"

        return SceneResponse(
            id=item_id,
            title=title,
            mission="Sentinel-2",
            sensor="Multispectral",
            platformId=platform,
            instrument="MSI (MultiSpectral Instrument)",
            acquisitionDate=dt,
            cloudCoverPercent=round(cloud_percent, 1),
            spatialResolutionMeters=10,
            crs=crs_str,
            sunElevationDeg=round(sun_elev, 1),
            sunAzimuthDeg=round(sun_azimuth, 1),
            processingLevel="Level-2A (Bottom of Atmosphere Surface Reflectance)",
            centerCoordinates=CenterCoordinates(lat=round(center_lat, 4), lon=round(center_lon, 4)),
            boundingBox=[round(c, 4) for c in bbox],
            locationName=location_name,
            orbitPass="Descending",
            relativeOrbitNumber=rel_orbit,
            bands=SENTINEL_2_BANDS,
            thumbnailSvgType="agricultural",
            stacSelfHref=self_href,
            dataSizeMb=round(float(props.get("s2:product_size", 650000000)) / (1024 * 1024), 1),
            isRealData=True,
            previewUrl=thumbnail_url,
        )

    async def search(self, parsed_query: ParsedQuery, limit: int = 10) -> list[SceneResponse]:
        raw_features = await stac_provider.search_scenes(
            bbox=parsed_query.bbox,
            datetime_range=parsed_query.datetime_range,
            max_cloud_cover=parsed_query.max_cloud_cover,
            limit=limit,
        )

        scenes = [
            self.transform_stac_feature(feat, parsed_query.location_name)
            for feat in raw_features
        ]
        return scenes


catalog_service = CatalogService()
