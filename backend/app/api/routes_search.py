import logging
from fastapi import APIRouter, HTTPException, status
from ..schemas.query import SearchQueryRequest
from ..schemas.scene import SceneResponse
from ..services.query_service import query_service, LocationResolutionError
from ..services.catalog_service import catalog_service
from ..providers.stac_provider import STACProviderError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Catalog Search"])


@router.post(
    "/search",
    response_model=list[SceneResponse],
    summary="Search real Sentinel-2 L2A scenes via public STAC catalog",
)
async def search_satellite_scenes(request: SearchQueryRequest) -> list[SceneResponse]:
    """Resolves natural language or structured search parameters and queries Earth Search STAC catalog."""
    try:
        parsed = query_service.parse_query(request)
    except LocationResolutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "LocationResolutionError",
                "message": str(exc),
            },
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "ValidationError",
                "message": str(exc),
            },
        ) from exc

    try:
        scenes = await catalog_service.search(parsed, limit=request.limit)
        return scenes
    except STACProviderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "STACProviderError",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during catalog search: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalSearchError",
                "message": f"Search failed: {str(exc)}",
            },
        ) from exc
