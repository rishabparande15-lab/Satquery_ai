from fastapi import APIRouter, HTTPException, status

from ..providers.stac_provider import STACProviderError, stac_provider
from ..schemas.validation import InputValidationResponse, ScenePairValidationRequest, ScenePairValidationResponse
from ..services.validation_service import validation_service

router = APIRouter(prefix="/api", tags=["Input & Geospatial Validation"])


@router.get("/scenes/{scene_id}/validation", response_model=InputValidationResponse)
async def validate_scene(scene_id: str) -> InputValidationResponse:
    try:
        item = await stac_provider.get_scene(scene_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"Scene '{scene_id}' not found in Sentinel-2 L2A STAC catalog.")
        return await validation_service.validate_live_item(item)
    except HTTPException:
        raise
    except STACProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/validation/pairs", response_model=ScenePairValidationResponse)
async def validate_scene_pair(request: ScenePairValidationRequest) -> ScenePairValidationResponse:
    try:
        before = await stac_provider.get_scene(request.before_scene_id)
        after = await stac_provider.get_scene(request.after_scene_id)
        if not before or not after:
            raise HTTPException(status_code=404, detail="One or both scenes were not found in the Sentinel-2 L2A STAC catalog.")
        return validation_service.validate_pair_metadata(before, after)
    except HTTPException:
        raise
    except STACProviderError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
