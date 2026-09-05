import logging
from fastapi import APIRouter, HTTPException, status
from ..schemas.scene import SceneDetailResponse
from ..services.catalog_service import catalog_service
from ..providers.stac_provider import stac_provider, STACProviderError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Scene Details"])


@router.get(
    "/scenes/{scene_id}",
    response_model=SceneDetailResponse,
    summary="Get real STAC metadata and asset links for a scene",
)
async def get_scene_details(scene_id: str) -> SceneDetailResponse:
    """Retrieves full STAC item from Earth Search Sentinel-2 collection."""
    try:
        item = await stac_provider.get_scene(scene_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scene '{scene_id}' not found in Sentinel-2 L2A STAC catalog.",
            )

        # Base scene transformation
        transformed = catalog_service.transform_stac_feature(
            item, location_name=f"Scene {scene_id}"
        )

        assets_raw = item.get("assets", {})
        assets_dict = {
            k: {
                "href": v.get("href"),
                "title": v.get("title"),
                "type": v.get("type"),
            }
            for k, v in assets_raw.items()
        }

        return SceneDetailResponse(
            **transformed.model_dump(),
            assets=assets_dict,
            stac_item_json=item,
        )

    except HTTPException:
        raise
    except STACProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error retrieving scene %s: %s", scene_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scene details: {str(exc)}",
        ) from exc
