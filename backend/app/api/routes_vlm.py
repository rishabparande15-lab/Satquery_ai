"""FastAPI endpoint for Multimodal Vision-Language Model (VLM) question-answering."""

import logging
from fastapi import APIRouter, HTTPException, status

from ..schemas.vlm import VLMQueryRequest, VLMQueryResponse
from ..services.vlm_service import (
    VLMBaseError,
    VLMConfigurationError,
    VLMSceneNotFoundError,
    VLMValidationError,
    VLMUnsupportedSceneError,
    VLMMissingAssetError,
    VLMTimeoutError,
    VLMProviderError,
    VLMMalformedResponseError,
    vlm_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vlm", tags=["Multimodal Vision-Language (VLM)"])


@router.post(
    "/ask",
    response_model=VLMQueryResponse,
    summary="Ask a natural-language question about a satellite scene using multimodal VLM",
    responses={
        200: {"description": "Grounded question-answering synthesis completed successfully."},
        404: {"description": "Target STAC scene was not found."},
        422: {"description": "Scene failed geospatial validation, unsupported modality, or missing visual asset."},
        502: {"description": "Upstream VLM provider failure or malformed JSON completion."},
        503: {"description": "VLM provider not configured (missing API key or invalid settings)."},
        504: {"description": "VLM provider timed out."},
    },
)
async def ask_scene_vlm(request: VLMQueryRequest) -> VLMQueryResponse:
    """Answers user questions against a Sentinel-2 scene using a multimodal Vision-Language Model.

    Execution Flow:
    1. Validates provider credentials and model configuration.
    2. Resolves scene from Sentinel-2 L2A STAC catalog.
    3. Runs geospatial & modality validation guard.
    4. Downloads visual RGB asset and injects verified metadata.
    5. Dispatches request to configured multimodal provider (Gemini).
    6. Parses, validates, and returns structured answer, evidence citations, and confidence score.
    """
    try:
        return await vlm_service.ask_scene(request)
    except VLMConfigurationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "VLMConfigurationError",
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    except VLMSceneNotFoundError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "VLMSceneNotFoundError",
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    except (VLMValidationError, VLMUnsupportedSceneError, VLMMissingAssetError) as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    except VLMTimeoutError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": "VLMTimeoutError",
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    except (VLMProviderError, VLMMalformedResponseError) as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    except VLMBaseError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": exc.__class__.__name__,
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during VLM query execution: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "VLMExecutionError",
                "message": f"VLM execution failed: {str(exc)}",
            },
        ) from exc
