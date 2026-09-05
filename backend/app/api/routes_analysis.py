import logging
from fastapi import APIRouter, HTTPException, status
from ..schemas.analysis import NDVIAnalysisRequest, NDVIAnalysisResponse
from ..services.analysis_service import analysis_service
from ..processing.ndvi import RasterProcessingError
from ..providers.stac_provider import STACProviderError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Geospatial Processing"])


@router.post(
    "/analyze",
    response_model=NDVIAnalysisResponse,
    summary="Compute genuine NDVI over bounded window using remote COG streaming",
)
async def analyze_scene(request: NDVIAnalysisRequest) -> NDVIAnalysisResponse:
    """Retrieves Red (B04) and NIR (B08) rasters via Rasterio windowed reads and computes true NDVI statistics."""
    try:
        response = await analysis_service.run_ndvi_analysis(request)
        return response
    except RasterProcessingError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "RasterProcessingError",
                "message": str(exc),
            },
        ) from exc
    except STACProviderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "STACProviderError",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error in /api/analyze: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AnalysisExecutionError",
                "message": f"Analysis failed: {str(exc)}",
            },
        ) from exc
