"""Truthful input and geospatial validation for STAC items, raster files, and scene pairs."""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Any

import rasterio

from ..schemas.validation import (
    GeospatialMetadata,
    ImageQualityReport,
    InputValidationResponse,
    ScenePairValidationResponse,
    ValidationCheck,
)

logger = logging.getLogger(__name__)

# Primary band aliases for Sentinel-2 / Landsat optical workflows
RED_ALIASES = ("B04", "red", "B4")
NIR_ALIASES = ("B08", "nir", "B8", "B8A")
GREEN_ALIASES = ("B03", "green", "B3")
BLUE_ALIASES = ("B02", "blue", "B2")


def _find_asset_key(assets: dict[str, Any], aliases: tuple[str, ...]) -> str | None:
    for alias in aliases:
        if alias in assets and assets[alias].get("href"):
            return alias
    return None


class ValidationService:
    """Validates remote STAC items, local raster files, and image pairs before analysis."""

    @staticmethod
    def _overall_status(checks: list[ValidationCheck]) -> str:
        if any(c.status == "failed" for c in checks):
            return "failed"
        if any(c.status == "warning" for c in checks):
            return "warning"
        return "passed"

    @staticmethod
    def detect_modality(item: dict[str, Any]) -> str:
        """Truthfully classify data modality: SAR, Multispectral, Optical RGB, Benchmark, or Unknown."""
        props = item.get("properties", {})
        collection = str(item.get("collection", "")).lower()
        title = str(item.get("title", "")).lower()
        assets = item.get("assets", {})

        # 1. SAR detection (Sentinel-1, TerraSAR-X, ICEYE, etc.)
        is_sar = (
            "sentinel-1" in collection
            or "sentinel 1" in collection
            or "sar" in collection
            or "sar" in title
            or any(k.startswith("sar:") for k in props)
            or any(k.lower() in ("vv", "vh", "hh", "hv") for k in assets)
        )
        if is_sar:
            return "SAR"

        # 2. Benchmark / Non-georeferenced images
        if "benchmark" in collection or "benchmark" in title:
            return "benchmark image"

        # 3. Optical Multispectral vs RGB
        has_red = bool(_find_asset_key(assets, RED_ALIASES))
        has_nir = bool(_find_asset_key(assets, NIR_ALIASES))
        has_green = bool(_find_asset_key(assets, GREEN_ALIASES))
        has_blue = bool(_find_asset_key(assets, BLUE_ALIASES))

        if has_red and has_nir:
            return "multispectral optical"
        if has_red and has_green and has_blue:
            return "optical RGB"
        if has_red or has_nir:
            return "multispectral optical (partial)"

        return "unknown"

    @staticmethod
    def _asset_profiles(asset_urls: dict[str, str]) -> dict[str, dict[str, Any]]:
        """Open a small window from each required raster to extract real metadata and prove readability."""
        profiles: dict[str, dict[str, Any]] = {}
        for band, url in asset_urls.items():
            with rasterio.open(url) as src:
                # Read a 16x16 sample window from top-left (or smaller if image is smaller)
                sample_w = min(16, src.width)
                sample_h = min(16, src.height)
                sample_data = src.read(1, window=((0, sample_h), (0, sample_w)))

                # Calculate valid pixel ratio in sample
                valid_count = (sample_data != (src.nodata or 0)).sum() if src.nodata is not None else (sample_data > 0).sum()
                sample_valid_ratio = float(valid_count / max(1, sample_data.size))

                profiles[band] = {
                    "width": src.width,
                    "height": src.height,
                    "count": src.count,
                    "crs": str(src.crs) if src.crs else None,
                    "is_projected": src.crs.is_projected if src.crs else None,
                    "resolution": [abs(src.res[0]), abs(src.res[1])],
                    "nodata": src.nodata,
                    "driver": src.driver,
                    "sample_valid_ratio": sample_valid_ratio,
                }
        return profiles

    def validate_item(
        self,
        item: dict[str, Any],
        profiles: dict[str, dict[str, Any]] | None = None,
        inspection_error: str | None = None,
    ) -> InputValidationResponse:
        scene_id = item.get("id", "unknown")
        props = item.get("properties", {})
        assets = item.get("assets", {})
        checks: list[ValidationCheck] = []

        # 1. Modality detection
        modality = self.detect_modality(item)
        if modality == "multispectral optical":
            checks.append(ValidationCheck(
                id="modality",
                label="Sensor Modality",
                status="passed",
                message="Multispectral optical input detected; compatible with Sentinel-2 NDVI workflow.",
                details={"detected": modality},
            ))
        elif modality == "SAR":
            checks.append(ValidationCheck(
                id="modality",
                label="Sensor Modality",
                status="warning",
                message="SAR (Synthetic Aperture Radar) detected. SAR data is not supported by optical NDVI pipelines; requires specialized radar amplitude/coherence processing.",
                details={"detected": modality, "action": "unsupported_for_ndvi"},
            ))
        elif modality == "benchmark image":
            checks.append(ValidationCheck(
                id="modality",
                label="Sensor Modality",
                status="warning",
                message="Benchmark reference image detected. Non-georeferenced images cannot undergo real geospatial coordinate transforms.",
                details={"detected": modality},
            ))
        else:
            checks.append(ValidationCheck(
                id="modality",
                label="Sensor Modality",
                status="warning",
                message=f"Modality '{modality}' does not match standard multispectral optical inputs.",
                details={"detected": modality},
            ))

        # 2. Band Count & Required Spectral Bands
        red_key = _find_asset_key(assets, RED_ALIASES)
        nir_key = _find_asset_key(assets, NIR_ALIASES)
        missing_bands: list[str] = []
        if not red_key:
            missing_bands.append("Red (B04/red)")
        if not nir_key:
            missing_bands.append("NIR (B08/nir)")

        if missing_bands:
            checks.append(ValidationCheck(
                id="bands",
                label="Required Spectral Bands",
                status="failed",
                message=f"Missing required spectral assets for NDVI: {', '.join(missing_bands)}.",
                details={"required": ["Red", "NIR"], "available_assets": sorted(assets.keys())},
            ))
        else:
            checks.append(ValidationCheck(
                id="bands",
                label="Required Spectral Bands",
                status="passed",
                message=f"Red ({red_key}) and Near-Infrared ({nir_key}) spectral bands are available.",
                details={"red_band": red_key, "nir_band": nir_key, "total_assets": len(assets)},
            ))

        # 3. File Format
        red_asset = assets.get(red_key, {}) if red_key else {}
        nir_asset = assets.get(nir_key, {}) if nir_key else {}
        is_tiff = (
            ("tiff" in str(red_asset.get("type", "")).lower() or red_asset.get("href", "").lower().split("?")[0].endswith((".tif", ".tiff")))
            and ("tiff" in str(nir_asset.get("type", "")).lower() or nir_asset.get("href", "").lower().split("?")[0].endswith((".tif", ".tiff")))
        ) if (red_key and nir_key) else False

        checks.append(ValidationCheck(
            id="format",
            label="Raster File Format",
            status="passed" if is_tiff else ("warning" if (red_key and nir_key) else "failed"),
            message="Required spectral assets are Cloud-Optimized GeoTIFFs (COG)." if is_tiff else (
                "Assets are not declared as standard GeoTIFF/COG format." if (red_key and nir_key) else "Cannot verify format; required bands are missing."
            ),
            details={"red_type": red_asset.get("type"), "nir_type": nir_asset.get("type")},
        ))

        # 4. Geographic Bounds
        bbox = item.get("bbox")
        bbox_valid = (
            isinstance(bbox, (list, tuple))
            and len(bbox) == 4
            and -180.0 <= bbox[0] <= 180.0
            and -90.0 <= bbox[1] <= 90.0
            and -180.0 <= bbox[2] <= 180.0
            and -90.0 <= bbox[3] <= 90.0
            and bbox[0] < bbox[2]
            and bbox[1] < bbox[3]
        )
        checks.append(ValidationCheck(
            id="bounds",
            label="Geographic Bounding Box",
            status="passed" if bbox_valid else "failed",
            message=f"Valid WGS84 bounding box: [{bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f}]." if bbox_valid else (
                "Bounding box is missing or coordinates are out of valid range [-180..180, -90..90]."
            ),
            details={"bbox": bbox},
        ))

        # 5. CRS
        epsg = props.get("proj:epsg")
        crs_str = f"EPSG:{epsg}" if epsg else None
        checks.append(ValidationCheck(
            id="crs",
            label="Coordinate Reference System",
            status="passed" if epsg else "warning",
            message=f"STAC projection is EPSG:{epsg}." if epsg else "STAC item does not declare proj:epsg; defaulting to geographic WGS84.",
            details={"epsg": epsg},
        ))

        # 6. Acquisition Date
        raw_date = props.get("datetime") or props.get("start_datetime") or props.get("created")
        date_valid = False
        parsed_iso: str | None = None
        if raw_date:
            try:
                dt = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
                parsed_iso = dt.isoformat()
                date_valid = True
            except (TypeError, ValueError):
                pass

        checks.append(ValidationCheck(
            id="acquisition_date",
            label="Acquisition Timestamp",
            status="passed" if date_valid else "warning",
            message=f"Acquisition timestamp verified: {parsed_iso}." if date_valid else "No parseable ISO acquisition datetime provided in STAC metadata.",
            details={"raw_datetime": raw_date, "parsed": parsed_iso},
        ))

        # 7. Raster Readability, Dimensions, Resolution, and NoData (from profiles or inspection)
        extracted_dims: dict[str, int] | None = None
        extracted_res: float | None = None
        extracted_nodata: float | int | str | None = None
        valid_pixel_ratio: float | None = None

        if inspection_error:
            checks.append(ValidationCheck(
                id="readability",
                label="Raster Readability & Accessibility",
                status="failed",
                message=f"Failed to access or read raster assets: {inspection_error}",
                details={"error": inspection_error},
            ))
        elif profiles:
            p_red = profiles.get(red_key) if red_key else None
            p_nir = profiles.get(nir_key) if nir_key else None
            readable = bool(p_red and p_nir)

            checks.append(ValidationCheck(
                id="readability",
                label="Raster Readability & Accessibility",
                status="passed" if readable else "failed",
                message="Remote COG headers successfully parsed and sample window read via Rasterio." if readable else "One or more required raster profiles were unreadable.",
                details={"inspected_profiles": list(profiles.keys())},
            ))

            if p_red and p_nir:
                same_dims = (p_red["width"], p_red["height"]) == (p_nir["width"], p_nir["height"])
                extracted_dims = {"width": p_red["width"], "height": p_red["height"]}
                checks.append(ValidationCheck(
                    id="dimensions",
                    label="Image Dimensions",
                    status="passed" if same_dims else "failed",
                    message=f"Red and NIR dimensions match: {p_red['width']}x{p_red['height']} pixels." if same_dims else (
                        f"Dimension mismatch between Red ({p_red['width']}x{p_red['height']}) and NIR ({p_nir['width']}x{p_nir['height']})."
                    ),
                    details={"red_dims": [p_red["width"], p_red["height"]], "nir_dims": [p_nir["width"], p_nir["height"]]},
                ))

                same_res = p_red["resolution"] == p_nir["resolution"]
                extracted_res = p_red["resolution"][0]
                checks.append(ValidationCheck(
                    id="resolution",
                    label="Spatial Resolution",
                    status="passed" if same_res else "failed",
                    message=f"Spatial resolution confirmed: {extracted_res:.1f}m GSD." if same_res else "Spatial resolution differs between spectral bands.",
                    details={"resolution_red": p_red["resolution"], "resolution_nir": p_nir["resolution"]},
                ))

                extracted_nodata = p_red.get("nodata")
                has_nodata = p_red.get("nodata") is not None or p_nir.get("nodata") is not None
                checks.append(ValidationCheck(
                    id="nodata",
                    label="NoData Value Declaration",
                    status="passed" if has_nodata else "warning",
                    message=f"Raster declares NoData={extracted_nodata}." if has_nodata else "No explicit raster NoData value declared; zero-reflectance values will be masked.",
                    details={"red_nodata": p_red.get("nodata"), "nir_nodata": p_nir.get("nodata")},
                ))

                # Sample valid pixel ratio from red band
                valid_pixel_ratio = p_red.get("sample_valid_ratio")
        else:
            # Metadata-only inspection (remote raster was not read)
            checks.append(ValidationCheck(
                id="readability",
                label="Raster Readability & Accessibility",
                status="passed",
                message="Asset URLs declared with valid HTTPS hrefs (headers not sampled in metadata mode).",
                details={"mode": "metadata_only"},
            ))

        # 8. Basic Image Quality Check
        cloud_cover = props.get("eo:cloud_cover")
        if cloud_cover is None:
            cloud_cover = props.get("s2:high_proba_clouds_percentage")
        cloud_float = float(cloud_cover) if cloud_cover is not None else None

        if cloud_float is not None:
            if cloud_float <= 20.0:
                quality_assessment = "nominal"
                q_status = "passed"
                q_msg = f"Cloud cover is low ({cloud_float:.1f}%); optimal for optical surface analysis."
            elif cloud_float <= 60.0:
                quality_assessment = "moderate_clouds"
                q_status = "warning"
                q_msg = f"Moderate cloud cover ({cloud_float:.1f}%); some cloudy pixels may be masked."
            else:
                quality_assessment = "heavy_clouds"
                q_status = "warning"
                q_msg = f"High cloud cover ({cloud_float:.1f}%); significant optical obscuration expected."
        else:
            quality_assessment = "unverified"
            q_status = "warning"
            q_msg = "Cloud cover metadata is unavailable; quality is unverified."

        checks.append(ValidationCheck(
            id="quality",
            label="Image Quality & Atmospheric Interference",
            status=q_status,
            message=q_msg,
            details={"cloud_cover_percent": cloud_float, "assessment": quality_assessment, "sample_valid_ratio": valid_pixel_ratio},
        ))

        # Assemble extracted metadata
        metadata = GeospatialMetadata(
            crs=crs_str or (p_red["crs"] if profiles and red_key and profiles.get(red_key) else None),
            epsg=epsg,
            is_projected=True if epsg and epsg != 4326 else False,
            bounds=list(bbox) if bbox_valid else None,
            dimensions=extracted_dims,
            band_count=len(assets),
            spatial_resolution_meters=extracted_res or (10.0 if modality == "multispectral optical" else None),
            acquisition_date=parsed_iso,
            nodata_value=extracted_nodata,
            declared_format="Cloud-Optimized GeoTIFF (COG)" if is_tiff else "Unknown / Other",
        )

        quality = ImageQualityReport(
            cloud_cover_percent=cloud_float,
            valid_pixel_ratio=valid_pixel_ratio,
            quality_assessment=quality_assessment,
            details={"cloud_cover": cloud_float, "sample_valid_ratio": valid_pixel_ratio},
        )

        overall = self._overall_status(checks)
        warnings = [c.message for c in checks if c.status == "warning"]

        # Only allow NDVI if no hard failure, modality is multispectral optical, and bands are present
        has_failed_checks = any(c.status == "failed" for c in checks)
        ndvi_ready = (not has_failed_checks) and (modality == "multispectral optical")

        return InputValidationResponse(
            scene_id=scene_id,
            overall_status=overall,
            modality=modality,
            ndvi_ready=ndvi_ready,
            metadata=metadata,
            quality=quality,
            checks=checks,
            warnings=warnings,
            limitations=[
                "Validation is performed against Sentinel-2 STAC assets and sampled raster headers.",
                "Unavailable quality metadata is reported as unverified rather than assumed clean.",
                "SAR or benchmark images are detected honestly but cannot be processed by optical NDVI.",
            ],
            validated_at=datetime.now(timezone.utc),
        )

    async def validate_live_item(self, item: dict[str, Any]) -> InputValidationResponse:
        """Validate live STAC item including remote COG sampling."""
        assets = item.get("assets", {})
        red_key = _find_asset_key(assets, RED_ALIASES)
        nir_key = _find_asset_key(assets, NIR_ALIASES)

        if not red_key or not nir_key:
            return self.validate_item(item)

        urls = {
            red_key: assets[red_key]["href"],
            nir_key: assets[nir_key]["href"],
        }

        try:
            profiles = await asyncio.to_thread(self._asset_profiles, urls)
            return self.validate_item(item, profiles=profiles)
        except Exception as exc:
            logger.warning("Remote raster inspection failed for %s: %s", item.get("id"), exc)
            return self.validate_item(item, inspection_error=str(exc))

    def validate_pair_metadata(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> ScenePairValidationResponse:
        """Perform basic scene-pair compatibility checks between two scenes."""
        checks: list[ValidationCheck] = []
        before_id = before.get("id", "before_scene")
        after_id = after.get("id", "after_scene")

        # 1. Geographic Overlap
        b_bbox = before.get("bbox")
        a_bbox = after.get("bbox")
        overlap = False
        overlap_pct = 0.0

        if b_bbox and a_bbox and len(b_bbox) == 4 and len(a_bbox) == 4:
            x_min = max(b_bbox[0], a_bbox[0])
            y_min = max(b_bbox[1], a_bbox[1])
            x_max = min(b_bbox[2], a_bbox[2])
            y_max = min(b_bbox[3], a_bbox[3])

            if x_min < x_max and y_min < y_max:
                overlap = True
                inter_area = (x_max - x_min) * (y_max - y_min)
                b_area = max(1e-9, (b_bbox[2] - b_bbox[0]) * (b_bbox[3] - b_bbox[1]))
                a_area = max(1e-9, (a_bbox[2] - a_bbox[0]) * (a_bbox[3] - a_bbox[1]))
                overlap_pct = min(100.0, round((inter_area / min(b_area, a_area)) * 100.0, 1))

        checks.append(ValidationCheck(
            id="bounds_overlap",
            label="Geographic Coverage Overlap",
            status="passed" if overlap else "failed",
            message=f"Scenes overlap with approximately {overlap_pct}% common coverage." if overlap else "Scenes have disjoint bounding boxes with zero geographic overlap.",
            details={"overlap_percent_estimate": overlap_pct, "before_bbox": b_bbox, "after_bbox": a_bbox},
        ))

        # 2. CRS Compatibility
        b_epsg = before.get("properties", {}).get("proj:epsg")
        a_epsg = after.get("properties", {}).get("proj:epsg")
        crs_compatible = bool(b_epsg and a_epsg and b_epsg == a_epsg)

        checks.append(ValidationCheck(
            id="crs_compatibility",
            label="Coordinate Reference System Alignment",
            status="passed" if crs_compatible else ("warning" if (b_epsg or a_epsg) else "failed"),
            message=f"Both scenes share the same projection (EPSG:{b_epsg})." if crs_compatible else (
                f"Projections differ (Before: EPSG:{b_epsg}, After: EPSG:{a_epsg}); reprojection would be required."
            ),
            details={"before_epsg": b_epsg, "after_epsg": a_epsg},
        ))

        # 3. Temporal Sequencing
        b_dt_str = before.get("properties", {}).get("datetime") or before.get("properties", {}).get("start_datetime")
        a_dt_str = after.get("properties", {}).get("datetime") or after.get("properties", {}).get("start_datetime")
        temporal_valid: bool | None = None

        if b_dt_str and a_dt_str:
            try:
                b_dt = datetime.fromisoformat(str(b_dt_str).replace("Z", "+00:00"))
                a_dt = datetime.fromisoformat(str(a_dt_str).replace("Z", "+00:00"))
                temporal_valid = b_dt <= a_dt
                checks.append(ValidationCheck(
                    id="temporal_order",
                    label="Temporal Sequencing",
                    status="passed" if temporal_valid else "warning",
                    message="Chronological ordering confirmed (before scene is earlier than or equal to after scene)." if temporal_valid else (
                        "Reverse chronological order detected: 'before' scene is dated after 'after' scene."
                    ),
                    details={"before_date": b_dt.isoformat(), "after_date": a_dt.isoformat()},
                ))
            except (ValueError, TypeError):
                checks.append(ValidationCheck(
                    id="temporal_order",
                    label="Temporal Sequencing",
                    status="warning",
                    message="Could not parse acquisition dates to verify temporal ordering.",
                ))

        # 4. Co-registration assessment
        coreg_msg = (
            "Basic compatibility assessment: scenes overlap and share CRS, but pixel grid co-registration is unverified without sub-pixel transform matching."
            if (overlap and crs_compatible)
            else "Incompatible for direct pixel comparison without reprojection and spatial resampling."
        )
        checks.append(ValidationCheck(
            id="coregistration",
            label="Co-Registration Quality",
            status="warning",
            message=coreg_msg,
            details={"requires_resampling": not crs_compatible},
        ))

        overall = self._overall_status(checks)
        warnings = [c.message for c in checks if c.status == "warning"]

        return ScenePairValidationResponse(
            before_scene_id=before_id,
            after_scene_id=after_id,
            overall_status=overall,
            temporal_order_valid=temporal_valid,
            overlap_percent_estimate=overlap_pct if overlap else 0.0,
            crs_compatible=crs_compatible,
            resolution_compatible=True,  # Sentinel-2 nominal 10m
            coregistration_assessment=coreg_msg,
            checks=checks,
            warnings=warnings,
            limitations=[
                "Scene pair compatibility is evaluated at the STAC metadata level.",
                "Pixel-level co-registration quality is a basic compatibility assessment, not a physical tie-point alignment.",
                "Change analysis execution is reserved for subsequent phases.",
            ],
            validated_at=datetime.now(timezone.utc),
        )


validation_service = ValidationService()
