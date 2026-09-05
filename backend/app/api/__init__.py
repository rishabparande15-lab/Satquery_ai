from .routes_health import router as health_router
from .routes_search import router as search_router
from .routes_scenes import router as scenes_router
from .routes_analysis import router as analysis_router

__all__ = ["health_router", "search_router", "scenes_router", "analysis_router"]
