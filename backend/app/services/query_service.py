import re
from datetime import datetime, timedelta, timezone
from ..schemas.query import SearchQueryRequest, ParsedQuery


class LocationResolutionError(Exception):
    """Raised when query references an unknown location and no explicit bbox was provided."""

    def __init__(self, message: str):
        super().__init__(message)


# Deterministic curated dictionary of benchmark Earth observation locations
KNOWN_LOCATIONS: dict[str, dict] = {
    "bengaluru": {
        "name": "Bengaluru, India",
        "bbox": [77.45, 12.85, 77.75, 13.15],
    },
    "bangalore": {
        "name": "Bengaluru, India",
        "bbox": [77.45, 12.85, 77.75, 13.15],
    },
    "rotterdam": {
        "name": "Port of Rotterdam, Netherlands",
        "bbox": [3.95, 51.85, 4.30, 52.05],
    },
    "amazon": {
        "name": "Amazon Basin (Altamira / Pará), Brazil",
        "bbox": [-52.45, -3.65, -51.92, -3.19],
    },
    "para": {
        "name": "Amazon Basin (Altamira / Pará), Brazil",
        "bbox": [-52.45, -3.65, -51.92, -3.19],
    },
    "nile": {
        "name": "Nile Delta, Egypt",
        "bbox": [30.12, 30.72, 30.84, 31.33],
    },
    "cairo": {
        "name": "Nile River Corridor / Cairo, Egypt",
        "bbox": [31.15, 29.95, 31.45, 30.15],
    },
    "san francisco": {
        "name": "San Francisco Bay Area, USA",
        "bbox": [-122.52, 37.45, -122.15, 37.85],
    },
    "silicon valley": {
        "name": "San Francisco Bay Area, USA",
        "bbox": [-122.52, 37.45, -122.15, 37.85],
    },
    "valencia": {
        "name": "Valencia Region, Spain",
        "bbox": [-0.55, 39.18, -0.15, 39.50],
    },
    "paris": {
        "name": "Paris Region, France",
        "bbox": [2.15, 48.75, 2.55, 48.95],
    },
    "london": {
        "name": "Greater London, United Kingdom",
        "bbox": [-0.35, 51.35, 0.15, 51.65],
    },
    "greenland": {
        "name": "Jakobshavn Glacier, West Greenland",
        "bbox": [-50.35, 68.95, -49.30, 69.40],
    },
    "tokyo": {
        "name": "Tokyo Bay, Japan",
        "bbox": [139.60, 35.50, 140.00, 35.80],
    },
}


class QueryService:
    """Parses natural-language or structured query input into validated STAC parameters."""

    def parse_query(self, req: SearchQueryRequest) -> ParsedQuery:
        query_text = (req.query or "").strip()
        query_lower = query_text.lower()

        # 1. Resolve Bounding Box
        bbox = req.bbox
        location_name = "Custom Bounding Box"

        if bbox is not None:
            if len(bbox) != 4:
                raise ValueError("Bounding box must contain exactly 4 coordinates: [minLon, minLat, maxLon, maxLat].")
            min_lon, min_lat, max_lon, max_lat = bbox
            if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180 and -90 <= min_lat <= 90 and -90 <= max_lat <= 90):
                raise ValueError("Bounding box coordinates out of valid WGS84 range.")
            if min_lon > max_lon or min_lat > max_lat:
                raise ValueError("Bounding box invalid: min coordinate exceeds max coordinate.")
            location_name = f"AOI [{min_lon:.2f}, {min_lat:.2f}, {max_lon:.2f}, {max_lat:.2f}]"
        else:
            # Check for explicit lat/lon in query (e.g. "lat: 12.9, lon: 77.6" or "12.97, 77.59")
            coord_match = re.search(r"(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)", query_text)
            if coord_match:
                try:
                    c1, c2 = float(coord_match.group(1)), float(coord_match.group(2))
                    # Determine lat/lon vs lon/lat
                    lat, lon = (c1, c2) if -90 <= c1 <= 90 and -180 <= c2 <= 180 else (c2, c1)
                    # Create 0.2 degree buffer around point
                    bbox = [lon - 0.1, lat - 0.1, lon + 0.1, lat + 0.1]
                    location_name = f"Coordinate AOI ({lat:.3f}°, {lon:.3f}°)"
                except Exception:
                    pass

            # Match against known locations
            if bbox is None:
                matched = False
                for key, loc in KNOWN_LOCATIONS.items():
                    if key in query_lower:
                        bbox = loc["bbox"]
                        location_name = loc["name"]
                        matched = True
                        break

                if not matched:
                    if not query_text:
                        # Fallback default: Bengaluru agricultural/urban corridor
                        bbox = KNOWN_LOCATIONS["bengaluru"]["bbox"]
                        location_name = KNOWN_LOCATIONS["bengaluru"]["name"]
                    else:
                        raise LocationResolutionError(
                            f"Location referenced in '{query_text}' is not in the deterministic catalog "
                            f"and no bounding box was specified. Supported demo locations: "
                            f"{', '.join([k.title() for k in KNOWN_LOCATIONS.keys()])}. "
                            f"Alternatively, provide explicit bbox coordinates: [minLon, minLat, maxLon, maxLat]."
                        )

        # 2. Resolve Date Range (RFC 3339 format required by STAC)
        now = datetime.now(timezone.utc)
        if req.start_date and req.end_date:
            try:
                s_dt = datetime.fromisoformat(req.start_date.replace("Z", "+00:00"))
                e_dt = datetime.fromisoformat(req.end_date.replace("Z", "+00:00"))
                s_str = s_dt.strftime("%Y-%m-%dT00:00:00Z")
                e_str = e_dt.strftime("%Y-%m-%dT23:59:59Z")
                datetime_range = f"{s_str}/{e_str}"
            except ValueError as exc:
                raise ValueError("Invalid ISO date format provided for start_date or end_date.") from exc
        else:
            # Default to past 180 days to ensure ample Sentinel-2 coverage
            start = (now - timedelta(days=180)).strftime("%Y-%m-%dT00:00:00Z")
            end = now.strftime("%Y-%m-%dT23:59:59Z")
            datetime_range = f"{start}/{end}"

        # 3. Resolve Cloud Cover
        max_cloud = req.max_cloud_cover
        cloud_match = re.search(r"cloud\s*(?:<=|<|under)?\s*(\d+)%?", query_lower)
        if cloud_match:
            try:
                max_cloud = float(cloud_match.group(1))
            except Exception:
                pass

        return ParsedQuery(
            bbox=bbox,
            datetime_range=datetime_range,
            max_cloud_cover=max_cloud,
            location_name=location_name,
            mission=req.mission,
        )


query_service = QueryService()
