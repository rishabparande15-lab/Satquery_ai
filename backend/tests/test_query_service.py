import pytest
from backend.app.services.query_service import query_service, LocationResolutionError
from backend.app.schemas.query import SearchQueryRequest


def test_parse_known_location_bengaluru():
    req = SearchQueryRequest(query="Find Sentinel-2 imagery of Bengaluru with cloud <= 15%")
    parsed = query_service.parse_query(req)
    assert parsed.location_name == "Bengaluru, India"
    assert parsed.bbox == [77.45, 12.85, 77.75, 13.15]
    assert parsed.max_cloud_cover == 15.0


def test_parse_known_location_rotterdam():
    req = SearchQueryRequest(query="Water turbidity in Rotterdam")
    parsed = query_service.parse_query(req)
    assert "Rotterdam" in parsed.location_name
    assert parsed.bbox == [3.95, 51.85, 4.30, 52.05]


def test_parse_explicit_bbox():
    req = SearchQueryRequest(bbox=[10.0, 45.0, 11.0, 46.0], max_cloud_cover=10.0)
    parsed = query_service.parse_query(req)
    assert parsed.bbox == [10.0, 45.0, 11.0, 46.0]
    assert parsed.max_cloud_cover == 10.0


def test_parse_explicit_coordinates_in_text():
    req = SearchQueryRequest(query="Observations near 51.95, 4.12")
    parsed = query_service.parse_query(req)
    assert len(parsed.bbox) == 4
    # Bounding box should surround 4.12, 51.95
    assert parsed.bbox[0] < 4.12 < parsed.bbox[2]
    assert parsed.bbox[1] < 51.95 < parsed.bbox[3]


def test_unknown_location_raises_error():
    req = SearchQueryRequest(query="Imagery over Atlantis fictional city")
    with pytest.raises(LocationResolutionError) as excinfo:
        query_service.parse_query(req)
    assert "not in the deterministic catalog" in str(excinfo.value)


def test_invalid_bbox_raises_error():
    # minLon > maxLon
    req = SearchQueryRequest(bbox=[80.0, 12.0, 70.0, 13.0])
    with pytest.raises(ValueError) as excinfo:
        query_service.parse_query(req)
    assert "min coordinate exceeds max coordinate" in str(excinfo.value)


def test_out_of_range_bbox_raises_error():
    req = SearchQueryRequest(bbox=[-200.0, 10.0, 10.0, 15.0])
    with pytest.raises(ValueError) as excinfo:
        query_service.parse_query(req)
    assert "WGS84 range" in str(excinfo.value)
