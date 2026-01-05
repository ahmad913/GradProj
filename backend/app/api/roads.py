from fastapi import APIRouter, HTTPException
from app.core.geometry import validate_polygon
from app.core.osm import fetch_roads_from_polygon
from app.core.sampling import generate_candidate_points

router = APIRouter()


@router.post("/roads/from_polygon")
def roads_from_polygon(payload: dict):
    try:
        coords = payload.get("polygon")
        spacing = payload.get("sampling_interval_m", 25)

        if not coords:
            raise ValueError("Missing polygon coordinates")

        # Validate polygon (WGS84)
        polygon = validate_polygon(coords)

        # Fetch roads (WGS84)
        roads = fetch_roads_from_polygon(polygon)

        # Project to metric CRS (Web Mercator)
        roads = roads.set_crs("EPSG:4326").to_crs("EPSG:3857")

        # Generate candidate points
        candidates = generate_candidate_points(roads, spacing)

        # Convert back to WGS84 for output
        roads = roads.to_crs("EPSG:4326")
        candidates = candidates.to_crs("EPSG:4326")

        return {
            "roads": roads.__geo_interface__,
            "candidates": candidates.__geo_interface__
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
