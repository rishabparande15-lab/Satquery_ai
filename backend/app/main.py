import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .api import health_router, search_router, scenes_router, analysis_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log startup summary so Render deploy logs confirm the app is live."""
    routes = [r.path for r in app.routes]  # type: ignore[attr-defined]
    logger.info(
        "SatQuery AI API v%s started | environment=%s | routes=%s",
        settings.version,
        settings.environment,
        routes,
    )
    yield
    logger.info("SatQuery AI API shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Earth Observation STAC discovery and real-time NDVI processing engine",
    lifespan=lifespan,
)

# CORS middleware for local frontend and production Netlify domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(health_router)
app.include_router(search_router)
app.include_router(scenes_router)
app.include_router(analysis_router)


@app.get("/")
def root() -> dict[str, str]:
    """Root endpoint — returns service identity, version, and status."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "ok",
        "docs": "/docs",
    }