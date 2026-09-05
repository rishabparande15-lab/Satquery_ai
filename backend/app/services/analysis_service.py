import logging
import time
from datetime import datetime, timezone
from ..providers.stac_provider import stac_provider
from ..processing.ndvi import compute_bounded_ndvi, RasterProcessingError
from ..schemas.analysis import (
    NDVIAnalysisRequest,
    NDVIAnalysisResponse,
    VegetationDensityBreakdown,
    MetricDeltaItem,
)
from ..config import get_settings

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates Sentinel-2 asset discovery, windowed NDVI extraction, and truthful reporting."""

    def __init__(self):
        self.settings = get_settings()

    async def run_ndvi_analysis(self, request: NDVIAnalysisRequest) -> NDVIAnalysisResponse:
        scene_id = request.scene_id
        logger.info("Starting real NDVI analysis workflow for scene: %s", scene_id)

        # 1. Resolve STAC item
        stac_item = await stac_provider.get_scene(scene_id)
        if not stac_item:
            raise RasterProcessingError(
                f"Scene '{scene_id}' not found in public Sentinel-2 STAC catalog.",
                status_code=404,
            )

        assets = stac_item.get("assets", {})

        # 2. Locate Red (B04) and NIR (B08) COG asset URLs
        red_href = None
        nir_href = None

        # Earth Search uses 'red' / 'nir' or band keys
        if "red" in assets:
            red_href = assets["red"].get("href")
        elif "B04" in assets:
            red_href = assets["B04"].get("href")

        if "nir" in assets:
            nir_href = assets["nir"].get("href")
        elif "B08" in assets:
            nir_href = assets["B08"].get("href")

        if not red_href or not nir_href:
            available_keys = list(assets.keys())
            raise RasterProcessingError(
                f"Scene '{scene_id}' is missing required spectral bands for NDVI. "
                f"Requires Red (B04) and NIR (B08). Available assets: {available_keys}",
                status_code=422,
            )

        # 3. Execute bounded window NDVI calculation via Rasterio
        window_size = min(request.window_pixels, self.settings.max_analysis_window_pixels)
        stats = compute_bounded_ndvi(
            red_asset_url=red_href,
            nir_asset_url=nir_href,
            window_pixels=window_size,
            max_window_pixels=self.settings.max_analysis_window_pixels,
        )

        job_id = f"real-ndvi-{int(time.time() * 1000)}"
        now_iso = datetime.now(timezone.utc).isoformat()

        mean_ndvi = stats.get("mean_ndvi")
        valid_px = stats.get("valid_pixels", 0)
        total_px = stats.get("total_pixels", 0)
        area_km = stats.get("area_analyzed_sq_km", 0.0)

        # 4. Construct truthful executive summary and key findings
        if valid_px > 0 and mean_ndvi is not None:
            veg_density = stats["vegetation_density"]
            summary = (
                f"REAL SENTINEL-2 L2A ANALYSIS: Bounded raster window ({window_size}x{window_size} pixels, "
                f"{area_km:.2f} km²) analyzed at 10m spatial resolution. Mean surface NDVI is {mean_ndvi:.3f} "
                f"(range: [{stats['min_ndvi']:.3f}, {stats['max_ndvi']:.3f}]). "
                f"Vegetation density: {veg_density['dense_canopy_percent']:.1f}% dense canopy, "
                f"{veg_density['moderate_vegetation_percent']:.1f}% moderate vegetation, "
                f"{veg_density['sparse_vegetation_percent']:.1f}% sparse, and "
                f"{veg_density['non_vegetated_or_water_percent']:.1f}% non-vegetated/water."
            )
            key_findings = [
                f"Analyzed {valid_px:,} valid surface reflectance pixels ({valid_px/total_px*100:.1f}% coverage).",
                f"Mean NDVI index: {mean_ndvi:.3f} across target bounded AOI.",
                f"NIR (B08) and Red (B04) read directly from public AWS Sentinel-2 Cloud-Optimized GeoTIFFs.",
                f"Nodata/invalid pixels masked: {stats['nodata_pixels']:,} pixels.",
            ]
        else:
            summary = (
                f"REAL SENTINEL-2 L2A ANALYSIS: Bounded window read completed ({area_km:.2f} km²), "
                f"but 100% of sampled pixels were masked as nodata or water."
            )
            key_findings = [
                "No valid non-zero surface reflectance pixels in the selected center window.",
                "Target window may fall on scene border or open water body.",
            ]

        # Metric deltas: strictly report baseline without fabricating changes
        metric_deltas = [
            MetricDeltaItem(
                label="Mean NDVI",
                value=f"{mean_ndvi:.3f}" if mean_ndvi is not None else "N/A",
                change=None,
                trend="stable",
                baseline="Single observation (temporal delta unavailable)",
                unit="index",
            ),
            MetricDeltaItem(
                label="Sampled Footprint",
                value=f"{area_km:.2f} km²",
                change=None,
                trend="stable",
                baseline=f"{window_size}x{window_size} pixels @ 10m GSD",
                unit="km²",
            ),
            MetricDeltaItem(
                label="Valid Pixel Ratio",
                value=f"{(valid_px / total_px * 100.0):.1f}%" if total_px > 0 else "0%",
                change=None,
                trend="stable",
                baseline=f"{valid_px:,} of {total_px:,} px",
                unit="%",
            ),
        ]

        methodology = (
            "Computed using Rasterio windowed streaming over AWS Sentinel-2 L2A Cloud-Optimized GeoTIFFs. "
            "Formula: NDVI = (NIR - Red) / (NIR + Red) where Red = B04 (665nm) and NIR = B08 (842nm). "
            "DN scale factor 1/10000 applied per ESA Sentinel-2 L2A surface reflectance specification."
        )

        limitations = (
            "SCIENTIFIC LIMITATIONS: Computed on a single acquisition window. "
            "Atmospheric correction performed by ESA Sen2Cor ground segment. "
            "No change detection, time-series anomaly modeling, or machine learning classification "
            "was performed. Uncalibrated cloud shadows or water bodies may affect local values."
        )

        return NDVIAnalysisResponse(
            job_id=job_id,
            scene_id=scene_id,
            mission="Sentinel-2",
            query=request.query or f"NDVI analysis of {scene_id}",
            timestamp=now_iso,
            status="completed",
            valid_pixels=valid_px,
            total_pixels=total_px,
            nodata_pixels=stats.get("nodata_pixels", 0),
            area_analyzed_sq_km=area_km,
            spatial_resolution_meters=10.0,
            min_ndvi=stats.get("min_ndvi"),
            max_ndvi=stats.get("max_ndvi"),
            mean_ndvi=mean_ndvi,
            median_ndvi=stats.get("median_ndvi"),
            std_ndvi=stats.get("std_ndvi"),
            vegetation_density=VegetationDensityBreakdown(
                non_vegetated_or_water_percent=stats["vegetation_density"]["non_vegetated_or_water_percent"],
                sparse_vegetation_percent=stats["vegetation_density"]["sparse_vegetation_percent"],
                moderate_vegetation_percent=stats["vegetation_density"]["moderate_vegetation_percent"],
                dense_canopy_percent=stats["vegetation_density"]["dense_canopy_percent"],
            ),
            source_assets={"red": red_href, "nir": nir_href},
            confidence_score_percent=None,
            anomalies_detected_count=None,
            metric_deltas=metric_deltas,
            executive_summary=summary,
            key_findings=key_findings,
            methodology=methodology,
            limitations=limitations,
            processing_duration_ms=stats.get("processing_duration_ms", 0),
            is_real_analysis=True,
        )


analysis_service = AnalysisService()
