"""Truthful unit and integration tests for Phase 2 Input and Geospatial Validation."""

from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.validation_service import validation_service
from backend.app.schemas.validation import InputValidationResponse, ScenePairValidationResponse


@pytest.fixture
def mock_sentinel2_stac_item():
    return {
        "id": "S2A_MSIL2A_20240618T104512_N0510_R051_T31UFS",
        "collection": "sentinel-2-l2a",
        "bbox": [2.30, 48.80, 2.45, 48.95],
        "properties": {
            "platform": "sentinel-2a",
            "datetime": "2024-06-18T10:45:12Z",
            "proj:epsg": 32631,
            "eo:cloud_cover": 8.5,
        },
        "assets": {
            "B04": {
                "href": "https://sentinel-cogs.s3.amazonaws.com/sentinel-s2-l2a-cogs/31/U/FS/2024/6/S2A_31UFS_20240618_0_L2A/B04.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            },
            "B08": {
                "href": "https://sentinel-cogs.s3.amazonaws.com/sentinel-s2-l2a-cogs/31/U/FS/2024/6/S2A_31UFS_20240618_0_L2A/B08.tif",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
            },
            "visual": {
                "href": "https://sentinel-cogs.s3.amazonaws.com/sentinel-s2-l2a-cogs/31/U/FS/2024/6/S2A_31UFS_20240618_0_L2A/TCI.tif",
                "type": "image/tiff",
            },
        },
    }


@pytest.fixture
def mock_sar_stac_item():
    return {
        "id": "S1A_IW_GRDH_1SDV_20240618T053000",
        "collection": "sentinel-1-grd",
        "bbox": [12.0, 41.0, 13.0, 42.0],
        "properties": {
            "platform": "sentinel-1a",
            "datetime": "2024-06-18T05:30:00Z",
            "sar:instrument_mode": "IW",
            "sar:polarizations": ["VV", "VH"],
        },
        "assets": {
            "vv": {"href": "https://sar.example.com/vv.tif", "type": "image/tiff"},
            "vh": {"href": "https://sar.example.com/vh.tif", "type": "image/tiff"},
        },
    }


def test_validate_valid_sentinel2_scene(mock_sentinel2_stac_item):
    report = validation_service.validate_item(mock_sentinel2_stac_item)
    assert report.overall_status == "passed"
    assert report.modality == "multispectral optical"
    assert report.ndvi_ready is True
    assert report.metadata.epsg == 32631
    assert report.metadata.is_projected is True
    assert report.metadata.bounds == [2.30, 48.80, 2.45, 48.95]
    assert report.metadata.spatial_resolution_meters == 10.0
    assert report.quality.quality_assessment == "nominal"
    assert report.quality.cloud_cover_percent == 8.5


def test_validate_alias_bands_red_nir():
    item = {
        "id": "S2_ALIASES",
        "collection": "sentinel-2-l2a",
        "bbox": [10.0, 10.0, 11.0, 11.0],
        "properties": {"datetime": "2024-05-01T12:00:00Z", "proj:epsg": 32632, "eo:cloud_cover": 5.0},
        "assets": {
            "red": {"href": "https://cogs.example.com/red.tif", "type": "image/tiff"},
            "nir": {"href": "https://cogs.example.com/nir.tif", "type": "image/tiff"},
        },
    }
    report = validation_service.validate_item(item)
    assert report.overall_status == "passed"
    assert report.ndvi_ready is True
    assert report.modality == "multispectral optical"
    band_check = next(c for c in report.checks if c.id == "bands")
    assert band_check.status == "passed"
    assert "red" in band_check.message
    assert "nir" in band_check.message


def test_validate_missing_nir_fails(mock_sentinel2_stac_item):
    del mock_sentinel2_stac_item["assets"]["B08"]
    report = validation_service.validate_item(mock_sentinel2_stac_item)
    assert report.overall_status == "failed"
    assert report.ndvi_ready is False
    band_check = next(c for c in report.checks if c.id == "bands")
    assert band_check.status == "failed"
    assert "Missing required spectral assets" in band_check.message


def test_validate_invalid_bbox_fails(mock_sentinel2_stac_item):
    mock_sentinel2_stac_item["bbox"] = [200.0, 50.0, 10.0, 40.0]  # out of range & min > max
    report = validation_service.validate_item(mock_sentinel2_stac_item)
    assert report.overall_status == "failed"
    bounds_check = next(c for c in report.checks if c.id == "bounds")
    assert bounds_check.status == "failed"


def test_validate_sar_modality_detected(mock_sar_stac_item):
    report = validation_service.validate_item(mock_sar_stac_item)
    assert report.modality == "SAR"
    assert report.ndvi_ready is False
    assert report.overall_status == "failed"  # Missing optical bands fails
    modality_check = next(c for c in report.checks if c.id == "modality")
    assert modality_check.status == "warning"
    assert "SAR" in modality_check.message


def test_validate_unverified_quality_when_cloud_cover_absent(mock_sentinel2_stac_item):
    del mock_sentinel2_stac_item["properties"]["eo:cloud_cover"]
    report = validation_service.validate_item(mock_sentinel2_stac_item)
    assert report.quality.quality_assessment == "unverified"
    quality_check = next(c for c in report.checks if c.id == "quality")
    assert quality_check.status == "warning"
    assert "unverified" in quality_check.message.lower()


def test_validate_with_raster_profiles(mock_sentinel2_stac_item):
    profiles = {
        "B04": {
            "width": 10980,
            "height": 10980,
            "count": 1,
            "crs": "EPSG:32631",
            "is_projected": True,
            "resolution": [10.0, 10.0],
            "nodata": 0.0,
            "driver": "GTiff",
            "sample_valid_ratio": 0.95,
        },
        "B08": {
            "width": 10980,
            "height": 10980,
            "count": 1,
            "crs": "EPSG:32631",
            "is_projected": True,
            "resolution": [10.0, 10.0],
            "nodata": 0.0,
            "driver": "GTiff",
            "sample_valid_ratio": 0.96,
        },
    }
    report = validation_service.validate_item(mock_sentinel2_stac_item, profiles=profiles)
    assert report.overall_status == "passed"
    assert report.metadata.dimensions == {"width": 10980, "height": 10980}
    assert report.metadata.nodata_value == 0.0
    dim_check = next(c for c in report.checks if c.id == "dimensions")
    assert dim_check.status == "passed"


def test_validate_raster_dimension_mismatch(mock_sentinel2_stac_item):
    profiles = {
        "B04": {
            "width": 10980,
            "height": 10980,
            "count": 1,
            "crs": "EPSG:32631",
            "resolution": [10.0, 10.0],
            "nodata": 0.0,
            "driver": "GTiff",
            "sample_valid_ratio": 0.9,
        },
        "B08": {
            "width": 5490,  # mismatch!
            "height": 5490,
            "count": 1,
            "crs": "EPSG:32631",
            "resolution": [20.0, 20.0],
            "nodata": 0.0,
            "driver": "GTiff",
            "sample_valid_ratio": 0.9,
        },
    }
    report = validation_service.validate_item(mock_sentinel2_stac_item, profiles=profiles)
    assert report.overall_status == "failed"
    dim_check = next(c for c in report.checks if c.id == "dimensions")
    assert dim_check.status == "failed"


def test_scene_pair_validation_overlapping_compatible():
    before = {
        "id": "S2A_20240101",
        "bbox": [10.0, 50.0, 11.0, 51.0],
        "properties": {"proj:epsg": 32632, "datetime": "2024-01-01T10:00:00Z"},
    }
    after = {
        "id": "S2B_20240601",
        "bbox": [10.2, 50.2, 11.2, 51.2],
        "properties": {"proj:epsg": 32632, "datetime": "2024-06-01T10:00:00Z"},
    }
    pair_report = validation_service.validate_pair_metadata(before, after)
    assert pair_report.crs_compatible is True
    assert pair_report.temporal_order_valid is True
    assert pair_report.overlap_percent_estimate > 0.0
    assert "basic compatibility assessment" in pair_report.coregistration_assessment.lower()


def test_scene_pair_validation_disjoint():
    before = {
        "id": "S2_EUROPE",
        "bbox": [10.0, 50.0, 11.0, 51.0],
        "properties": {"proj:epsg": 32632, "datetime": "2024-01-01T10:00:00Z"},
    }
    after = {
        "id": "S2_INDIA",
        "bbox": [77.0, 12.0, 78.0, 13.0],
        "properties": {"proj:epsg": 32643, "datetime": "2024-06-01T10:00:00Z"},
    }
    pair_report = validation_service.validate_pair_metadata(before, after)
    assert pair_report.overall_status == "failed"
    assert pair_report.overlap_percent_estimate == 0.0
    assert pair_report.crs_compatible is False


def test_scene_pair_validation_reverse_chronological():
    before = {
        "id": "S2_LATER",
        "bbox": [10.0, 50.0, 11.0, 51.0],
        "properties": {"proj:epsg": 32632, "datetime": "2024-09-01T10:00:00Z"},
    }
    after = {
        "id": "S2_EARLIER",
        "bbox": [10.0, 50.0, 11.0, 51.0],
        "properties": {"proj:epsg": 32632, "datetime": "2024-01-01T10:00:00Z"},
    }
    pair_report = validation_service.validate_pair_metadata(before, after)
    assert pair_report.temporal_order_valid is False
    temp_check = next(c for c in pair_report.checks if c.id == "temporal_order")
    assert temp_check.status == "warning"


def test_api_scene_validation_endpoint(mock_sentinel2_stac_item):
    client = TestClient(app)
    with patch("backend.app.providers.stac_provider.stac_provider.get_scene", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sentinel2_stac_item
        resp = client.get("/api/scenes/mock_scene_id/validation")
        assert resp.status_code == 200
        data = resp.json()
        assert data["scene_id"] == mock_sentinel2_stac_item["id"]
        assert data["overall_status"] == "passed"
        assert data["ndvi_ready"] is True
        assert data["metadata"]["epsg"] == 32631


def test_api_scene_pair_validation_endpoint(mock_sentinel2_stac_item):
    client = TestClient(app)
    second_item = dict(mock_sentinel2_stac_item)
    second_item["id"] = "S2_SECOND"
    second_item["properties"] = dict(mock_sentinel2_stac_item["properties"])
    second_item["properties"]["datetime"] = "2024-07-01T10:00:00Z"

    with patch("backend.app.providers.stac_provider.stac_provider.get_scene", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = lambda sid: mock_sentinel2_stac_item if sid == "scene_1" else second_item
        resp = client.post("/api/validation/pairs", json={"before_scene_id": "scene_1", "after_scene_id": "scene_2"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["crs_compatible"] is True
        assert data["temporal_order_valid"] is True


def test_analysis_guard_blocks_unsupported_scene(mock_sar_stac_item):
    """Confirm analysis service guard refuses non-optical / missing-band inputs before processing."""
    client = TestClient(app)
    with patch("backend.app.providers.stac_provider.stac_provider.get_scene", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_sar_stac_item
        resp = client.post("/api/analyze", json={"scene_id": "sar_scene_1", "window_pixels": 64})
        assert resp.status_code == 422
        err_msg = resp.json()["detail"]["message"]
        assert "validation failed" in err_msg.lower()
