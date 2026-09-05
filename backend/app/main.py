from fastapi import FastAPI

from .config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": settings.app_name, "status": "ok"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "satquery-ai-api"}