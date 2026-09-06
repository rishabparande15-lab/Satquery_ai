from datetime import datetime, timezone
from fastapi import APIRouter
from ..schemas.health import HealthResponse
from ..config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
@router.get("/api/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Returns backend system status, version, active mode, and capabilities."""
    settings = get_settings()
    providers = ["earth-search-stac"]
    capabilities = [
        "sentinel-2-l2a-search",
        "bounded-window-ndvi",
        "remote-cog-streaming",
        "input-geospatial-validation",
        "pair-compatibility-check",
    ]

    # Report VLM capability only when the provider is genuinely configured with a valid API key
    if settings.gemini_api_key and settings.gemini_api_key.strip():
        providers.append(settings.vlm_model if "gemini" in settings.vlm_model else f"gemini-{settings.vlm_model}")
        capabilities.append("multimodal-vlm-qa")

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.version,
        active_mode="live",
        providers=providers,
        capabilities=capabilities,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
