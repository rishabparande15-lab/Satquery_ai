from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SatQuery AI API"
    version: str = "0.1.0"
    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    # Public STAC API Provider (AWS Earth Search - Sentinel-2 L2A)
    stac_api_url: str = "https://earth-search.aws.element84.com/v1"
    stac_collection: str = "sentinel-2-l2a"
    stac_timeout_seconds: float = 12.0

    # Geospatial analysis window constraints
    max_analysis_window_pixels: int = 512  # Maximum dimension for real-time window read

    # Multimodal Vision-Language Model (VLM) settings
    vlm_provider: str = "gemini"
    gemini_api_key: str | None = None
    vlm_model: str = "gemini-2.5-flash"
    vlm_timeout_seconds: float = 30.0

    # CORS configuration
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://taupe-meringue-0cdf17.netlify.app",
    ]
    cors_origin_regex: str = r"^https://.*\.netlify\.app$"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()