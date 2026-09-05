import tempfile
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from fastapi.testclient import TestClient
from backend.app.processing.ndvi import compute_bounded_ndvi
from backend.app.main import app

client = TestClient(app)


def test_controlled_ndvi_formula_and_nodata():
    """Unit test NDVI calculation on synthetic rasters with known values."""
    width, height = 100, 100
    transform = from_origin(100000, 200000, 10, 10)

    # Synthetic Red band:
    red_data = np.full((height, width), 1000, dtype=np.uint16)
    red_data[50:, :] = 2000
    red_data[0, 0] = 0
    red_data[0, -1] = 0
    red_data[-1, 0] = 0
    red_data[-1, -1] = 0

    # Synthetic NIR band:
    nir_data = np.full((height, width), 3000, dtype=np.uint16)
    nir_data[50:, :] = 6000
    nir_data[45:55, 45:55] = 9000
    red_data[45:55, 45:55] = 1000
    nir_data[0, 0] = 0
    nir_data[0, -1] = 0
    nir_data[-1, 0] = 0
    nir_data[-1, -1] = 0

    with tempfile.NamedTemporaryFile(suffix="_red.tif", delete=False) as f_red, tempfile.NamedTemporaryFile(
        suffix="_nir.tif", delete=False
    ) as f_nir:
        red_path = f_red.name
        nir_path = f_nir.name

    meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "uint16",
        "crs": "EPSG:32643",
        "transform": transform,
        "nodata": 0,
    }

    with rasterio.open(red_path, "w", **meta) as dst_r:
        dst_r.write(red_data, 1)

    with rasterio.open(nir_path, "w", **meta) as dst_n:
        dst_n.write(nir_data, 1)

    # Execute bounded NDVI calculation
    result = compute_bounded_ndvi(
        red_asset_url=red_path,
        nir_asset_url=nir_path,
        window_pixels=100,
        max_window_pixels=200,
    )

    assert result["total_pixels"] == 10000
    assert result["nodata_pixels"] == 4
    assert result["valid_pixels"] == 9996

    assert pytest.approx(result["min_ndvi"], abs=0.01) == 0.50
    assert pytest.approx(result["max_ndvi"], abs=0.01) == 0.80
    assert 0.50 <= result["mean_ndvi"] <= 0.51
    assert result["median_ndvi"] == 0.50
    assert result["area_analyzed_sq_km"] == 1.0


def test_all_nodata_raster():
    """Test handling of 100% nodata/zero pixels."""
    width, height = 64, 64
    transform = from_origin(100000, 200000, 10, 10)
    zeros = np.zeros((height, width), dtype=np.uint16)

    with tempfile.NamedTemporaryFile(suffix="_z1.tif", delete=False) as f1, tempfile.NamedTemporaryFile(
        suffix="_z2.tif", delete=False
    ) as f2:
        p1, p2 = f1.name, f2.name

    meta = {
        "driver": "GTiff",
        "height": height,
        "width": width,
        "count": 1,
        "dtype": "uint16",
        "crs": "EPSG:32643",
        "transform": transform,
    }

    with rasterio.open(p1, "w", **meta) as d1:
        d1.write(zeros, 1)
    with rasterio.open(p2, "w", **meta) as d2:
        d2.write(zeros, 1)

    result = compute_bounded_ndvi(p1, p2, window_pixels=64)
    assert result["valid_pixels"] == 0
    assert result["mean_ndvi"] is None
    assert result["warnings"] is not None


def test_analyze_endpoint_with_real_scene():
    """Tests POST /api/analyze with a real scene found via search."""
    search_resp = client.post("/api/search", json={"query": "Bengaluru", "limit": 1})
    assert search_resp.status_code == 200
    scenes = search_resp.json()
    assert len(scenes) > 0

    real_scene_id = scenes[0]["id"]
    analyze_resp = client.post(
        "/api/analyze",
        json={
            "scene_id": real_scene_id,
            "query": "Assess vegetation health around Bengaluru",
            "window_pixels": 128,
        },
    )
    assert analyze_resp.status_code == 200
    res = analyze_resp.json()
    assert res["status"] == "completed"
    assert res["scene_id"] == real_scene_id
    assert res["is_real_analysis"] is True
    assert res["valid_pixels"] > 0
    assert res["mean_ndvi"] is not None
    assert res["confidence_score_percent"] is None  # Scientifically honest null
    assert "source_assets" in res
    assert "methodology" in res
    assert "limitations" in res
