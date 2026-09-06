"""Unit and integration tests for Multimodal Vision-Language Model (VLM) foundation."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient
import httpx

from backend.app.main import app
from backend.app.config import get_settings
from backend.app.schemas.vlm import VLMQueryRequest, VLMQueryResponse
from backend.app.services.vlm_service import (
    VLMConfigurationError,
    VLMMalformedResponseError,
    VLMMissingAssetError,
    VLMProviderError,
    VLMSceneNotFoundError,
    VLMTimeoutError,
    VLMUnsupportedSceneError,
    VLMValidationError,
    vlm_service,
)

client = TestClient(app)

# Minimal 1x1 valid JPEG byte sequence for image mocking
MINIMAL_JPEG_BYTES = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4"
    b"\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9"
)


@pytest.fixture
def mock_valid_sentinel2_stac():
    return {
        "id": "S2A_MSIL2A_20240618T104512_N0510_R051_T31UFS",
        "collection": "sentinel-2-l2a",
        "bbox": [2.30, 48.80, 2.45, 48.95],
        "properties": {
            "platform": "sentinel-2a",
            "datetime": "2024-06-18T10:45:12Z",
            "proj:epsg": 32631,
            "eo:cloud_cover": 4.5,
        },
        "assets": {
            "B04": {
                "href": "https://sentinel-cogs.s3.amazonaws.com/B04.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            },
            "B08": {
                "href": "https://sentinel-cogs.s3.amazonaws.com/B08.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            },
            "thumbnail": {
                "href": "https://sentinel-cogs.s3.amazonaws.com/preview.jpg",
                "type": "image/jpeg",
            },
        },
    }


@pytest.fixture
def mock_gemini_success_completion():
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": json.dumps(
                                {
                                    "answer": "The satellite observation reveals dense urban fabric surrounded by active agricultural zones along the river plain.",
                                    "confidence_score": 0.85,
                                    "confidence_level": "high",
                                    "evidence": [
                                        {
                                            "feature": "Urban Grid",
                                            "observation": "High density impervious surfaces and orthogonal street layout",
                                            "confidence": "high",
                                        },
                                        {
                                            "feature": "River Plain",
                                            "observation": "Curvilinear water body with low visible reflectance",
                                            "confidence": "high",
                                        },
                                    ],
                                    "limitations": [
                                        "10m visible resolution limits detection to macroscopic structures."
                                    ],
                                }
                            )
                        }
                    ],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ]
    }


# ---------------------------------------------------------------------------
# Test 1: Successful structured VLM response (Service & API integration)
# ---------------------------------------------------------------------------
def test_vlm_successful_query(mock_valid_sentinel2_stac, mock_gemini_success_completion):
    async def _run():
        with patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
             patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
             patch.object(get_settings(), "gemini_api_key", "test-secret-gemini-key-12345"):

            mock_stac.return_value = mock_valid_sentinel2_stac
            mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_gemini_success_completion
            mock_post.return_value = mock_resp

            req = VLMQueryRequest(
                scene_id="S2A_MSIL2A_20240618T104512_N0510_R051_T31UFS",
                question="What are the prominent land cover types in this scene?",
                include_ndvi_context=False,
            )

            response = await vlm_service.ask_scene(req)

            assert isinstance(response, VLMQueryResponse)
            assert response.scene_id == req.scene_id
            assert "urban fabric" in response.answer
            assert response.confidence_score == 0.85
            assert response.confidence_level == "high"
            assert len(response.evidence) == 2
            assert response.evidence[0].feature == "Urban Grid"
            assert "gemini/" in response.model_used
            assert response.latency_ms >= 0

    import anyio
    anyio.run(_run)


def test_api_vlm_ask_success(mock_valid_sentinel2_stac, mock_gemini_success_completion):
    with patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
         patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch.object(get_settings(), "gemini_api_key", "test-secret-gemini-key-12345"):

        mock_stac.return_value = mock_valid_sentinel2_stac
        mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gemini_success_completion
        mock_post.return_value = mock_resp

        payload = {
            "scene_id": "S2A_MSIL2A_20240618T104512_N0510_R051_T31UFS",
            "question": "Analyze the agricultural coverage.",
            "include_ndvi_context": False,
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["confidence_score"] == 0.85
        assert len(data["evidence"]) == 2
        assert "timestamp" in data


# ---------------------------------------------------------------------------
# Test 2: Missing API key returns honest configuration error (HTTP 503)
# ---------------------------------------------------------------------------
def test_vlm_missing_api_key_returns_503():
    with patch.object(get_settings(), "gemini_api_key", None):
        payload = {
            "scene_id": "S2A_MSIL2A_20240618T104512",
            "question": "What is in this image?",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 503
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMConfigurationError"
        assert "GEMINI_API_KEY" in detail.get("message", "")


# ---------------------------------------------------------------------------
# Test 3: Invalid scene ID returns HTTP 404
# ---------------------------------------------------------------------------
def test_vlm_invalid_scene_returns_404():
    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac:
        mock_stac.return_value = None

        payload = {
            "scene_id": "NON_EXISTENT_SCENE_123",
            "question": "What is here?",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 404
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMSceneNotFoundError"


# ---------------------------------------------------------------------------
# Test 4: Validation rejection (corrupted metadata or missing bands)
# ---------------------------------------------------------------------------
def test_vlm_validation_rejection_returns_422(mock_valid_sentinel2_stac):
    # Keep optical bands so modality is optical, but corrupt bounds to trigger validation failure
    mock_valid_sentinel2_stac["bbox"] = [999.0, 999.0, -999.0, -999.0]

    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac:
        mock_stac.return_value = mock_valid_sentinel2_stac

        payload = {
            "scene_id": mock_valid_sentinel2_stac["id"],
            "question": "Can you analyze this scene?",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 422
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMValidationError"


# ---------------------------------------------------------------------------
# Test 5: Unsupported sensor modality (e.g. SAR Sentinel-1)
# ---------------------------------------------------------------------------
def test_vlm_unsupported_sar_modality_returns_422():
    sar_item = {
        "id": "S1A_IW_GRDH_1SDV_20240618",
        "collection": "sentinel-1-grd",
        "bbox": [10.0, 45.0, 11.0, 46.0],
        "properties": {"platform": "sentinel-1a", "datetime": "2024-06-18T10:00:00Z"},
        "assets": {"vv": {"href": "https://sar.example.com/vv.tif", "type": "image/tiff"}},
    }
    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac:
        mock_stac.return_value = sar_item

        payload = {
            "scene_id": "S1A_IW_GRDH_1SDV_20240618",
            "question": "What is in this radar image?",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 422
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMUnsupportedSceneError"
        assert "SAR" in detail.get("message", "")


# ---------------------------------------------------------------------------
# Test 6: Missing visual RGB asset
# ---------------------------------------------------------------------------
def test_vlm_missing_visual_asset_returns_422(mock_valid_sentinel2_stac):
    # Remove all visual/thumbnail assets
    del mock_valid_sentinel2_stac["assets"]["thumbnail"]

    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac:
        mock_stac.return_value = mock_valid_sentinel2_stac

        payload = {
            "scene_id": mock_valid_sentinel2_stac["id"],
            "question": "Tell me about this image.",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 422
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMMissingAssetError"


# ---------------------------------------------------------------------------
# Test 7: Provider timeout returns HTTP 504
# ---------------------------------------------------------------------------
def test_vlm_provider_timeout_returns_504(mock_valid_sentinel2_stac):
    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
         patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
         patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Connection timed out")):

        mock_stac.return_value = mock_valid_sentinel2_stac
        mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

        payload = {
            "scene_id": mock_valid_sentinel2_stac["id"],
            "question": "Describe the forest canopy.",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 504
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMTimeoutError"


# ---------------------------------------------------------------------------
# Test 8: Provider HTTP failure (e.g. Upstream 400/500 from Gemini API)
# ---------------------------------------------------------------------------
def test_vlm_provider_http_error_returns_502(mock_valid_sentinel2_stac):
    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
         patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_stac.return_value = mock_valid_sentinel2_stac
        mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

        err_resp = MagicMock()
        err_resp.status_code = 400
        err_resp.text = '{"error": {"message": "Invalid argument: visual token exceeded"}}'
        err_resp.json.return_value = {"error": {"message": "Invalid argument: visual token exceeded"}}
        mock_post.return_value = err_resp

        payload = {
            "scene_id": mock_valid_sentinel2_stac["id"],
            "question": "Identify infrastructure.",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 502
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMProviderError"
        assert "Invalid argument" in detail.get("message", "")


# ---------------------------------------------------------------------------
# Test 9: Malformed provider JSON output returns HTTP 502
# ---------------------------------------------------------------------------
def test_vlm_malformed_provider_json_returns_502(mock_valid_sentinel2_stac):
    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
         patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_stac.return_value = mock_valid_sentinel2_stac
        mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

        # Gemini returns plain text rather than the required JSON object
        raw_completion = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "I see some clouds and water, but I will not output JSON."}],
                        "role": "model",
                    },
                    "finishReason": "STOP",
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = raw_completion
        mock_post.return_value = mock_resp

        payload = {
            "scene_id": mock_valid_sentinel2_stac["id"],
            "question": "Can you see clouds?",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 502
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMMalformedResponseError"


# ---------------------------------------------------------------------------
# Test 10: Invalid confidence score outside [0.0, 1.0] returns HTTP 502
# ---------------------------------------------------------------------------
def test_vlm_invalid_confidence_score_returns_502(mock_valid_sentinel2_stac):
    with patch.object(get_settings(), "gemini_api_key", "valid-key-xyz"), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
         patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_stac.return_value = mock_valid_sentinel2_stac
        mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

        # Confidence score 1.5 is outside [0.0, 1.0]
        invalid_score_completion = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "answer": "Land cover observed.",
                                        "confidence_score": 1.5,
                                        "confidence_level": "high",
                                        "evidence": [],
                                        "limitations": [],
                                    }
                                )
                            }
                        ],
                        "role": "model",
                    }
                }
            ]
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = invalid_score_completion
        mock_post.return_value = mock_resp

        payload = {
            "scene_id": mock_valid_sentinel2_stac["id"],
            "question": "What is the confidence?",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 502
        detail = res.json().get("detail", {})
        assert detail.get("error") == "VLMMalformedResponseError"


# ---------------------------------------------------------------------------
# Test 11: Correct metadata injection into prompt
# ---------------------------------------------------------------------------
def test_vlm_metadata_prompt_injection(mock_valid_sentinel2_stac, mock_gemini_success_completion):
    async def _run():
        with patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
             patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
             patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
             patch.object(get_settings(), "gemini_api_key", "test-key-xyz"):

            mock_stac.return_value = mock_valid_sentinel2_stac
            mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = mock_gemini_success_completion
            mock_post.return_value = mock_resp

            req = VLMQueryRequest(
                scene_id="S2A_MSIL2A_20240618T104512_N0510_R051_T31UFS",
                question="Where is the river located?",
                include_ndvi_context=False,
            )
            await vlm_service.ask_scene(req)

            # Inspect payload sent to Gemini API
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            sent_json = kwargs.get("json", {})
            user_text = sent_json["contents"][0]["parts"][1]["text"]

            # Verify exact grounded metadata presence
            assert "S2A_MSIL2A_20240618T104512_N0510_R051_T31UFS" in user_text
            assert "2024-06-18T10:45:12" in user_text
            assert "10.0m Ground Sample Distance" in user_text
            assert "4.5%" in user_text  # Cloud cover
            assert "EPSG:32631" in user_text
            assert "Where is the river located?" in user_text

    import anyio
    anyio.run(_run)


# ---------------------------------------------------------------------------
# Test 12: No secret leakage in error messages
# ---------------------------------------------------------------------------
def test_vlm_no_secret_leakage_in_errors(mock_valid_sentinel2_stac):
    secret_key = "synthetic-provider-key-" + "not-a-real-secret-999"

    with patch.object(get_settings(), "gemini_api_key", secret_key), \
         patch("backend.app.services.vlm_service.stac_provider.get_scene", new_callable=AsyncMock) as mock_stac, \
         patch("backend.app.services.vlm_service.vlm_service._fetch_visual_bytes", new_callable=AsyncMock) as mock_fetch, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:

        mock_stac.return_value = mock_valid_sentinel2_stac
        mock_fetch.return_value = (MINIMAL_JPEG_BYTES, "image/jpeg")

        # Simulate provider error echoing the API key in the response body
        mock_err_resp = MagicMock()
        mock_err_resp.status_code = 403
        mock_err_resp.text = f"Permission denied for key {secret_key}"
        mock_err_resp.json.return_value = {"error": {"message": f"Permission denied for key {secret_key}"}}
        mock_post.return_value = mock_err_resp

        payload = {
            "scene_id": mock_valid_sentinel2_stac["id"],
            "question": "Check security.",
        }
        res = client.post("/api/vlm/ask", json=payload)
        assert res.status_code == 502
        response_text = res.text

        # The raw secret must NEVER appear anywhere in the response
        assert secret_key not in response_text
        assert "[REDACTED_API_KEY]" in response_text


# ---------------------------------------------------------------------------
# Test 13: Health endpoint behavior (VLM reported only when configured)
# ---------------------------------------------------------------------------
def test_health_reports_vlm_only_when_configured():
    # When GEMINI_API_KEY is unset
    with patch.object(get_settings(), "gemini_api_key", None):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert "multimodal-vlm-qa" not in data["capabilities"]
        assert not any("gemini" in p for p in data["providers"])

    # When GEMINI_API_KEY is set
    with patch.object(get_settings(), "gemini_api_key", "real-or-test-key"):
        res = client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert "multimodal-vlm-qa" in data["capabilities"]
        assert any("gemini" in p for p in data["providers"])
