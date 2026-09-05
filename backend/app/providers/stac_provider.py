import logging
from typing import Any
import httpx
from ..config import get_settings

logger = logging.getLogger(__name__)


class STACProviderError(Exception):
    """Raised when an interaction with the external STAC catalog fails."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


class STACProvider:
    """Async client for public STAC APIs (Earth Search / AWS Sentinel-2 L2A)."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.stac_api_url.rstrip("/")
        self.collection = self.settings.stac_collection
        self.timeout = self.settings.stac_timeout_seconds

    async def search_scenes(
        self,
        bbox: list[float],
        datetime_range: str,
        max_cloud_cover: float = 20.0,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search Sentinel-2 L2A scenes in Earth Search STAC catalog."""
        search_url = f"{self.base_url}/search"
        payload = {
            "collections": [self.collection],
            "bbox": bbox,
            "datetime": datetime_range,
            "query": {
                "eo:cloud_cover": {"lte": max_cloud_cover},
            },
            "limit": limit,
            "sortby": [{"field": "properties.datetime", "direction": "desc"}],
        }

        logger.info(
            "STAC search request to %s with bbox=%s, datetime=%s, cloud_lte=%s",
            search_url,
            bbox,
            datetime_range,
            max_cloud_cover,
        )

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(search_url, json=payload)
                if response.status_code == 404:
                    return []
                response.raise_for_status()
                data = response.json()
                features = data.get("features", [])
                logger.info("STAC search returned %d features", len(features))
                return features

        except httpx.TimeoutException as exc:
            logger.error("STAC API timeout after %.1fs: %s", self.timeout, exc)
            raise STACProviderError(
                f"STAC catalog query timed out after {self.timeout}s.", status_code=504
            ) from exc
        except httpx.ConnectError as exc:
            logger.error("STAC API connection failed: %s", exc)
            raise STACProviderError(
                "Unable to connect to public STAC provider.", status_code=502
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error("STAC API returned HTTP %d: %s", exc.response.status_code, exc)
            raise STACProviderError(
                f"STAC catalog error (HTTP {exc.response.status_code}).",
                status_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            logger.exception("Unexpected error querying STAC provider: %s", exc)
            raise STACProviderError(
                f"Unexpected error communicating with STAC catalog: {str(exc)}",
                status_code=500,
            ) from exc

    async def get_scene(self, scene_id: str) -> dict[str, Any] | None:
        """Fetch full STAC metadata for a specific Sentinel-2 scene."""
        item_url = f"{self.base_url}/collections/{self.collection}/items/{scene_id}"
        logger.info("Fetching STAC item %s from %s", scene_id, item_url)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(item_url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            logger.error("Timeout fetching STAC item %s: %s", scene_id, exc)
            raise STACProviderError(f"Timeout fetching STAC item {scene_id}", status_code=504) from exc
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise STACProviderError(
                f"Error retrieving item {scene_id}: HTTP {exc.response.status_code}",
                status_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            logger.exception("Error retrieving STAC item %s: %s", scene_id, exc)
            raise STACProviderError(str(exc), status_code=500) from exc


stac_provider = STACProvider()
