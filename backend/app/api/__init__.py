from .routes_health import router as health_router
from .routes_search import router as search_router
from .routes_scenes import router as scenes_router
from .routes_analysis import router as analysis_router
from .routes_validation import router as validation_router
from .routes_vlm import router as vlm_router

__all__ = ["health_router", "search_router", "scenes_router", "analysis_router", "validation_router", "vlm_router"]
