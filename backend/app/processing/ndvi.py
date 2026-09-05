import logging
import time
import numpy as np
import rasterio
from rasterio.windows import Window

logger = logging.getLogger(__name__)


class RasterProcessingError(Exception):
    """Raised when remote raster access or NDVI calculation fails."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code


def compute_bounded_ndvi(
    red_asset_url: str,
    nir_asset_url: str,
    window_pixels: int = 256,
    max_window_pixels: int = 512,
) -> dict:
    """Computes genuine NDVI on a bounded window of Sentinel-2 L2A Red (B04) and NIR (B08) COGs.

    Mathematical definition:
        NDVI = (NIR - Red) / (NIR + Red)

    Uses Rasterio windowed reads with GDAL /vsicurl/ remote streaming.
    """
    start_time = time.perf_counter()
    w_size = max(64, min(window_pixels, max_window_pixels))

    logger.info(
        "Opening remote COGs with Rasterio for bounded NDVI: window=%dx%d",
        w_size,
        w_size,
    )

    try:
        with rasterio.open(red_asset_url) as src_r, rasterio.open(nir_asset_url) as src_n:
            if src_r.shape != src_n.shape:
                raise RasterProcessingError(
                    f"Dimension mismatch between Red ({src_r.shape}) and NIR ({src_n.shape}) rasters.",
                    status_code=422,
                )

            # Center window calculation
            center_col = src_r.width // 2
            center_row = src_r.height // 2
            half_w = w_size // 2

            window = Window(
                col_off=max(0, center_col - half_w),
                row_off=max(0, center_row - half_w),
                width=w_size,
                height=w_size,
            )

            # Read bounded window rasters
            red_arr = src_r.read(1, window=window).astype(np.float32)
            nir_arr = src_n.read(1, window=window).astype(np.float32)

    except rasterio.RasterioIOError as exc:
        logger.error("Rasterio IO error accessing COGs: %s", exc)
        raise RasterProcessingError(
            f"Failed to stream remote COG rasters via Rasterio: {str(exc)}",
            status_code=502,
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error reading remote rasters: %s", exc)
        raise RasterProcessingError(
            f"Raster processing error: {str(exc)}", status_code=500
        ) from exc

    total_pixels = int(red_arr.size)

    # Calculate NDVI safely without division warnings
    denom = nir_arr + red_arr
    valid_mask = (red_arr > 0) & (nir_arr > 0) & (denom > 0)
    valid_count = int(np.count_nonzero(valid_mask))
    nodata_count = total_pixels - valid_count

    # Resolution is 10 meters per pixel for B04 and B08
    spatial_resolution_m = 10.0
    area_sq_km = (total_pixels * (spatial_resolution_m * spatial_resolution_m)) / 1_000_000.0

    if valid_count == 0:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return {
            "valid_pixels": 0,
            "total_pixels": total_pixels,
            "nodata_pixels": nodata_count,
            "area_analyzed_sq_km": round(area_sq_km, 3),
            "spatial_resolution_meters": spatial_resolution_m,
            "min_ndvi": None,
            "max_ndvi": None,
            "mean_ndvi": None,
            "median_ndvi": None,
            "std_ndvi": None,
            "vegetation_density": {
                "non_vegetated_or_water_percent": 0.0,
                "sparse_vegetation_percent": 0.0,
                "moderate_vegetation_percent": 0.0,
                "dense_canopy_percent": 0.0,
            },
            "processing_duration_ms": duration_ms,
            "warnings": "Selected bounded window contains 100% nodata or water-masked pixels.",
        }

    # Calculate NDVI using safe division
    ndvi_arr = np.full(red_arr.shape, np.nan, dtype=np.float32)
    np.divide(nir_arr - red_arr, denom, out=ndvi_arr, where=valid_mask)
    valid_ndvi = ndvi_arr[valid_mask]

    min_ndvi = float(np.min(valid_ndvi))
    max_ndvi = float(np.max(valid_ndvi))
    mean_ndvi = float(np.mean(valid_ndvi))
    median_ndvi = float(np.median(valid_ndvi))
    std_ndvi = float(np.std(valid_ndvi))

    # Biological vegetation density distribution across valid pixels
    non_veg = float(np.count_nonzero(valid_ndvi < 0.1)) / valid_count * 100.0
    sparse_veg = float(np.count_nonzero((valid_ndvi >= 0.1) & (valid_ndvi < 0.3))) / valid_count * 100.0
    moderate_veg = float(np.count_nonzero((valid_ndvi >= 0.3) & (valid_ndvi < 0.6))) / valid_count * 100.0
    dense_veg = float(np.count_nonzero(valid_ndvi >= 0.6)) / valid_count * 100.0

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    logger.info(
        "NDVI computation complete: valid=%d/%d (%.1f%%), mean=%.3f in %dms",
        valid_count,
        total_pixels,
        (valid_count / total_pixels) * 100.0,
        mean_ndvi,
        duration_ms,
    )

    return {
        "valid_pixels": valid_count,
        "total_pixels": total_pixels,
        "nodata_pixels": nodata_count,
        "area_analyzed_sq_km": round(area_sq_km, 3),
        "spatial_resolution_meters": spatial_resolution_m,
        "min_ndvi": round(min_ndvi, 4),
        "max_ndvi": round(max_ndvi, 4),
        "mean_ndvi": round(mean_ndvi, 4),
        "median_ndvi": round(median_ndvi, 4),
        "std_ndvi": round(std_ndvi, 4),
        "vegetation_density": {
            "non_vegetated_or_water_percent": round(non_veg, 1),
            "sparse_vegetation_percent": round(sparse_veg, 1),
            "moderate_vegetation_percent": round(moderate_veg, 1),
            "dense_canopy_percent": round(dense_veg, 1),
        },
        "processing_duration_ms": duration_ms,
        "warnings": None,
    }
