from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_search_real_scenes_bengaluru():
    payload = {
        "query": "Sentinel-2 over Bengaluru",
        "max_cloud_cover": 30.0,
        "limit": 3,
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 200
    scenes = response.json()
    assert isinstance(scenes, list)
    assert len(scenes) > 0
    first = scenes[0]
    assert "Sentinel-2" in first["mission"]
    assert "Bengaluru" in first["locationName"]
    assert first["isRealData"] is True
    assert len(first["bands"]) == 11
    assert "centerCoordinates" in first
    assert len(first["boundingBox"]) == 4


def test_search_unknown_location_returns_400():
    payload = {"query": "Find images of Wakanda"}
    response = client.post("/api/search", json=payload)
    assert response.status_code == 400
    detail = response.json().get("detail", {})
    assert detail.get("error") == "LocationResolutionError"


def test_search_invalid_date_returns_400():
    payload = {
        "bbox": [77.4, 12.8, 77.8, 13.2],
        "start_date": "not-a-date",
        "end_date": "2024-01-01",
    }
    response = client.post("/api/search", json=payload)
    assert response.status_code == 400


def test_scene_details_not_found():
    response = client.get("/api/scenes/NON_EXISTENT_SCENE_XYZ")
    assert response.status_code == 404


def test_search_and_get_details():
    # First search
    search_resp = client.post(
        "/api/search", json={"query": "Rotterdam", "limit": 1}
    )
    assert search_resp.status_code == 200
    scenes = search_resp.json()
    if len(scenes) > 0:
        scene_id = scenes[0]["id"]
        detail_resp = client.get(f"/api/scenes/{scene_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["id"] == scene_id
        assert "assets" in detail
