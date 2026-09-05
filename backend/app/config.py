from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SatQuery AI API"
    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    ai_provider_api_key: str | None = None
    search_provider_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()