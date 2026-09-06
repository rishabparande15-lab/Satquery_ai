"""Multimodal Vision-Language Model (VLM) inference service for satellite imagery."""

import base64
from datetime import datetime, timezone
import io
import json
import logging
import time
from typing import Any
import httpx
from pydantic import ValidationError

from ..config import get_settings
from ..providers.stac_provider import stac_provider
from ..schemas.analysis import NDVIAnalysisRequest
from ..schemas.vlm import (
    VLMProviderStructuredOutput,
    VLMQueryRequest,
    VLMQueryResponse,
)
from ..services.analysis_service import analysis_service
from ..services.validation_service import validation_service

logger = logging.getLogger(__name__)

# Supported Gemini Multimodal Vision Models
SUPPORTED_GEMINI_MODELS: set[str] = {
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-8b",
    "gemini-1.5-pro",
    "gemini-1.5-pro-latest",
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-preview",
    "gemini-2.0-flash-lite-preview-02-05",
    "gemini-2.0-pro-exp-02-05",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
}

# Preferred visual asset keys in Sentinel-2 STAC metadata
VISUAL_ASSET_KEYS = ("thumbnail", "rendered_preview", "overview", "visual", "preview")

REMOTE_SENSING_SYSTEM_INSTRUCTION = """
You are SatQuery AI, an expert multimodal remote-sensing and Earth observation assistant.
Analyze the provided satellite image and verified metadata to answer the user's question with scientific rigor.

STRICT CONSTRAINTS & GUIDELINES:
1. Grounding: Rely ONLY on the provided image and verified scene metadata. Do NOT invent or hallucinate geographic, environmental, or infrastructural facts that are not clearly visible or directly supported.
2. Resolution limits: Sentinel-2 imagery has a nominal ground sample distance (GSD) of 10 meters per pixel for visible bands. Do NOT claim sub-meter or pixel-level certainty (e.g. do not claim to identify specific vehicle models, small individual objects, or exact species of trees).
3. Uncertainty & Limitations: Clearly state uncertainty when visual features are ambiguous, shaded, or obscured by clouds/haze.
4. Separation of Observations: Distinguish direct visual observations (colors, shapes, textures, spatial arrangements) from metadata-derived facts (acquisition date, satellite platform, UTM zone, NDVI statistics).
5. Atmospheric interference: If cloud cover or atmospheric scattering interferes with optical clarity, explicitly mention this in your answer and limitations.
6. Conservative Confidence: Assign conservative confidence values (0.0 to 1.0) and levels ('high', 'medium', 'low'). If visual evidence is partial or ambiguous, confidence MUST NOT be 'high'.
7. Output Format: You MUST respond ONLY with a valid JSON object strictly matching this schema:
{
  "answer": "<thorough, clear natural language answer addressing the question>",
  "confidence_score": <float between 0.0 and 1.0>,
  "confidence_level": "<high | medium | low>",
  "evidence": [
    {
      "feature": "<name of visual feature or region, e.g. Water Body, Agricultural Plots, Urban Grid>",
      "observation": "<specific visual or analytical evidence seen in the image>",
      "confidence": "<high | medium | low>"
    }
  ],
  "limitations": [
    "<limitation regarding 10m spatial resolution, cloud interference, single-observation temporal baseline, etc.>"
  ]
}
Do not include markdown fences (```json) or any conversational text outside the JSON object.
"""


class VLMBaseError(Exception):
    """Base exception for all VLM operations with an associated HTTP status code."""

    def __init__(self, message: str, status_code: int = 500, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class VLMConfigurationError(VLMBaseError):
    """Raised when VLM provider settings, API keys, or model configurations are missing or invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=503, details=details)


class VLMSceneNotFoundError(VLMBaseError):
    """Raised when the requested STAC scene cannot be found in the catalog."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=404, details=details)


class VLMValidationError(VLMBaseError):
    """Raised when the scene fails geospatial input validation."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=422, details=details)


class VLMUnsupportedSceneError(VLMBaseError):
    """Raised when the scene sensor modality is unsupported for optical VLM analysis."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=422, details=details)


class VLMMissingAssetError(VLMBaseError):
    """Raised when no accessible visual RGB asset or thumbnail can be obtained."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=422, details=details)


class VLMTimeoutError(VLMBaseError):
    """Raised when the VLM provider call times out."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=504, details=details)


class VLMProviderError(VLMBaseError):
    """Raised when the VLM provider returns an HTTP error status."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=502, details=details)


class VLMMalformedResponseError(VLMBaseError):
    """Raised when the VLM provider output cannot be parsed into the expected JSON schema."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, status_code=502, details=details)


def _sanitize_secret(text: str, secret: str | None) -> str:
    """Ensure API keys and credentials are never exposed in error messages or logs."""
    if not secret or len(secret) < 4:
        return text
    return text.replace(secret, "[REDACTED_API_KEY]")


def _clean_json_text(text: str) -> str:
    """Strip optional markdown code blocks (```json ... ```) from model completion."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("```"):
            lines = lines[1:]
        if len(lines) >= 1 and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


class VLMService:
    """Orchestrates grounded multimodal satellite question-answering via Gemini API."""

    def __init__(self):
        self.settings = get_settings()

    def _validate_configuration(self) -> tuple[str, str]:
        """Validates that provider API key and model configuration are set and supported."""
        api_key = self.settings.gemini_api_key
        if not api_key or not api_key.strip():
            raise VLMConfigurationError(
                "Gemini API key is not configured. Set the GEMINI_API_KEY environment variable to enable multimodal VLM question-answering."
            )

        model = self.settings.vlm_model
        if model not in SUPPORTED_GEMINI_MODELS and not model.startswith("gemini-"):
            raise VLMConfigurationError(
                f"Unsupported Gemini model '{model}'. Supported multimodal models include: {sorted(SUPPORTED_GEMINI_MODELS)}"
            )

        return api_key.strip(), model

    def _extract_visual_asset_url(self, item: dict[str, Any]) -> str:
        """Locates the best available visual RGB asset URL from STAC item assets."""
        assets = item.get("assets", {})
        if not assets:
            raise VLMMissingAssetError(f"Scene '{item.get('id')}' contains no STAC assets.")

        # 1. Prefer dedicated visual preview/thumbnail assets
        for key in VISUAL_ASSET_KEYS:
            if key in assets:
                href = assets[key].get("href")
                if href and str(href).startswith("http"):
                    return href

        # 2. Check for any asset declaring a web image MIME type
        for key, asset in assets.items():
            mime = str(asset.get("type", "")).lower()
            href = asset.get("href", "")
            if mime in ("image/jpeg", "image/png", "image/webp") and href.startswith("http"):
                return href

        # 3. Check for any asset with .jpg / .jpeg / .png in URL
        for key, asset in assets.items():
            href = str(asset.get("href", ""))
            clean_url = href.split("?")[0].lower()
            if clean_url.endswith((".jpg", ".jpeg", ".png", ".webp")):
                return href

        # 4. Check for 'visual' or 'TCI' GeoTIFF as fallback
        for key in ("visual", "tci", "TCI"):
            if key in assets and assets[key].get("href"):
                return assets[key]["href"]

        available_keys = sorted(assets.keys())
        raise VLMMissingAssetError(
            f"Scene '{item.get('id')}' has no accessible visual RGB preview asset for VLM inference. Available assets: {available_keys}"
        )

    async def _fetch_visual_bytes(self, url: str) -> tuple[bytes, str]:
        """Downloads visual asset bytes and returns (image_bytes, mime_type)."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise VLMMissingAssetError(
                        f"Failed to retrieve visual asset from '{url}': HTTP status {resp.status_code}"
                    )
                raw_bytes = resp.content
        except httpx.TimeoutException as exc:
            raise VLMMissingAssetError(f"Timeout fetching visual asset from '{url}': {exc}") from exc
        except Exception as exc:
            if isinstance(exc, VLMMissingAssetError):
                raise
            raise VLMMissingAssetError(f"Error accessing visual asset from '{url}': {exc}") from exc

        if not raw_bytes:
            raise VLMMissingAssetError(f"Retrieved 0 bytes for visual asset from '{url}'.")

        # Detect MIME type
        lower_url = url.split("?")[0].lower()
        mime_type = "image/jpeg"
        if lower_url.endswith(".png"):
            mime_type = "image/png"
        elif lower_url.endswith(".webp"):
            mime_type = "image/webp"

        # If it's a TIFF or COG, convert to JPEG via PIL
        if lower_url.endswith((".tif", ".tiff")) or raw_bytes[:4] in (b"II*\x00", b"MM\x00*"):
            try:
                from PIL import Image

                with Image.open(io.BytesIO(raw_bytes)) as img:
                    rgb_img = img.convert("RGB")
                    buf = io.BytesIO()
                    rgb_img.save(buf, format="JPEG", quality=85)
                    return buf.getvalue(), "image/jpeg"
            except Exception as exc:
                logger.warning("Could not convert TIFF asset to JPEG with PIL: %s", exc)
                return raw_bytes, "image/tiff"

        return raw_bytes, mime_type

    async def ask_scene(self, request: VLMQueryRequest) -> VLMQueryResponse:
        """Processes a natural-language question against a validated satellite scene."""
        start_time = time.perf_counter()
        scene_id = request.scene_id.strip()
        question = request.question.strip()

        logger.info("Starting VLM question-answering for scene '%s': '%s'", scene_id, question)

        # 1. Validate configuration and credentials
        api_key, model_name = self._validate_configuration()

        # 2. Retrieve STAC Scene
        stac_item = await stac_provider.get_scene(scene_id)
        if not stac_item:
            raise VLMSceneNotFoundError(
                f"Scene '{scene_id}' not found in Sentinel-2 L2A STAC catalog."
            )

        # 3. Validation Guard: Check modality first so unsupported modalities report clean modality rejection
        validation_report = validation_service.validate_item(stac_item)
        if validation_report.modality not in ("multispectral optical", "optical RGB"):
            raise VLMUnsupportedSceneError(
                f"Scene modality '{validation_report.modality}' is not supported for optical VLM analysis. "
                "Only optical multispectral or RGB imagery is supported."
            )

        if validation_report.overall_status == "failed":
            failed_reasons = [c.message for c in validation_report.checks if c.status == "failed"]
            reason_msg = "; ".join(failed_reasons) if failed_reasons else "Scene failed quality or metadata checks."
            raise VLMValidationError(
                f"Scene '{scene_id}' failed geospatial validation: {reason_msg}",
                details={"failed_checks": failed_reasons},
            )

        # 4. Extract visual RGB asset URL
        visual_url = self._extract_visual_asset_url(stac_item)

        # 5. Fetch visual asset bytes
        image_bytes, mime_type = await self._fetch_visual_bytes(visual_url)
        b64_image = base64.b64encode(image_bytes).decode("ascii")

        # 6. Assemble grounded geospatial metadata context
        metadata = validation_report.metadata
        quality = validation_report.quality
        props = stac_item.get("properties", {})

        acquisition_date = (
            metadata.acquisition_date
            or props.get("datetime")
            or props.get("created")
            or "Unknown acquisition date"
        )
        platform = props.get("platform", "Sentinel-2")
        crs_str = metadata.crs or "WGS 84 / Geographic"
        bounds_str = str(metadata.bounds) if metadata.bounds else str(stac_item.get("bbox", "Unknown"))
        cloud_pct = quality.cloud_cover_percent
        cloud_str = f"{cloud_pct:.1f}% ({quality.quality_assessment})" if cloud_pct is not None else "Unverified cloud cover"
        gsd_str = f"{metadata.spatial_resolution_meters or 10.0}m Ground Sample Distance (GSD)"

        # 7. Optionally retrieve real NDVI context
        ndvi_context: str | None = None
        if request.include_ndvi_context and validation_report.ndvi_ready:
            try:
                ndvi_res = await analysis_service.run_ndvi_analysis(
                    NDVIAnalysisRequest(scene_id=scene_id, window_pixels=256)
                )
                if ndvi_res.mean_ndvi is not None:
                    veg = ndvi_res.vegetation_density
                    ndvi_context = (
                        f"Mean NDVI: {ndvi_res.mean_ndvi:.3f} (Range: [{ndvi_res.min_ndvi:.3f}, {ndvi_res.max_ndvi:.3f}]). "
                        f"Vegetation breakdown: {veg.dense_canopy_percent:.1f}% dense canopy, "
                        f"{veg.moderate_vegetation_percent:.1f}% moderate vegetation, "
                        f"{veg.sparse_vegetation_percent:.1f}% sparse, "
                        f"{veg.non_vegetated_or_water_percent:.1f}% non-vegetated/water."
                    )
            except Exception as exc:
                logger.info("NDVI context not calculated for VLM query: %s", exc)

        user_prompt_text = (
            f"VERIFIED SATELLITE SCENE GROUNDED CONTEXT:\n"
            f"- Scene Identifier: {scene_id}\n"
            f"- Satellite Platform: {platform} (MSI Instrument)\n"
            f"- Acquisition Timestamp: {acquisition_date}\n"
            f"- Spatial Resolution: {gsd_str}\n"
            f"- Coordinate Reference System: {crs_str}\n"
            f"- Geographic Bounding Box [minLon, minLat, maxLon, maxLat]: {bounds_str}\n"
            f"- Cloud Cover Assessment: {cloud_str}\n"
        )
        if ndvi_context:
            user_prompt_text += f"- Biophysical NDVI Statistics: {ndvi_context}\n"

        user_prompt_text += (
            f"\nUSER QUESTION:\n\"{question}\"\n\n"
            f"Provide your scientifically truthful analysis in the required JSON format."
        )

        # 8. Dispatch request to Gemini API via httpx
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "system_instruction": {
                "parts": [{"text": REMOTE_SENSING_SYSTEM_INSTRUCTION.strip()}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_image,
                            }
                        },
                        {
                            "text": user_prompt_text,
                        },
                    ],
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.vlm_timeout_seconds) as client:
                response = await client.post(api_url, headers=headers, json=payload)
        except httpx.TimeoutException as exc:
            logger.error("Gemini VLM call timed out after %ss for scene %s", self.settings.vlm_timeout_seconds, scene_id)
            raise VLMTimeoutError(
                f"Gemini VLM provider timed out after {self.settings.vlm_timeout_seconds} seconds."
            ) from exc
        except Exception as exc:
            safe_err = _sanitize_secret(str(exc), api_key)
            logger.error("Network failure calling Gemini VLM API: %s", safe_err)
            raise VLMProviderError(f"Network error calling Gemini VLM: {safe_err}") from exc

        if response.status_code != 200:
            error_body = response.text
            safe_err = _sanitize_secret(error_body, api_key)
            try:
                err_json = response.json()
                api_msg = err_json.get("error", {}).get("message", safe_err)
                safe_err = _sanitize_secret(api_msg, api_key)
            except Exception:
                pass

            logger.warning("Gemini VLM provider returned HTTP %d: %s", response.status_code, safe_err)
            raise VLMProviderError(
                f"Gemini VLM provider error (HTTP {response.status_code}): {safe_err}"
            )

        # 9. Extract and validate structured response
        try:
            resp_data = response.json()
            candidates = resp_data.get("candidates", [])
            if not candidates:
                raise VLMMalformedResponseError("Gemini VLM returned no response candidates.")

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts or "text" not in parts[0]:
                raise VLMMalformedResponseError("Gemini VLM response contains no text content parts.")

            raw_text = parts[0]["text"]
            clean_text = _clean_json_text(raw_text)
            structured = VLMProviderStructuredOutput.model_validate_json(clean_text)

        except ValidationError as exc:
            safe_val_err = _sanitize_secret(str(exc), api_key)
            logger.warning("Gemini VLM response failed Pydantic schema validation: %s", safe_val_err)
            raise VLMMalformedResponseError(
                f"VLM provider response failed schema validation: {safe_val_err}"
            ) from exc
        except json.JSONDecodeError as exc:
            logger.warning("Gemini VLM response was not valid JSON: %s", exc)
            raise VLMMalformedResponseError(
                f"VLM provider returned malformed JSON: {str(exc)}"
            ) from exc
        except Exception as exc:
            if isinstance(exc, VLMMalformedResponseError):
                raise
            safe_err = _sanitize_secret(str(exc), api_key)
            logger.warning("Unexpected error parsing Gemini VLM response: %s", safe_err)
            raise VLMMalformedResponseError(f"Failed to process VLM response: {safe_err}") from exc

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        return VLMQueryResponse(
            scene_id=scene_id,
            question=question,
            answer=structured.answer,
            confidence_score=structured.confidence_score,
            confidence_level=structured.confidence_level,
            evidence=structured.evidence,
            limitations=structured.limitations,
            model_used=f"gemini/{model_name}",
            latency_ms=latency_ms,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


vlm_service = VLMService()
