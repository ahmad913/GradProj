from fastapi import APIRouter, HTTPException
from shapely.geometry import Polygon
import numpy as np
import pyproj

from app.core.osm import fetch_roads_from_polygon
from app.core.sampling import sample_points_on_roads
from app.optimization.pmedian import solve_p_median
from app.optimization.assign_lamps import assign_lamp_types

router = APIRouter()

project = pyproj.Transformer.from_crs(
    "EPSG:4326", "EPSG:3857", always_xy=True
).transform


@router.post("/optimize")
def optimize(payload: dict):

    try:
        polygon = Polygon(payload["polygon"])
        p = int(payload["p"])
        lamp_types = payload["lamp_types"]

        roads = fetch_roads_from_polygon(polygon)
        candidates = sample_points_on_roads(roads, spacing=30)

        if len(candidates) > 150:
            candidates = candidates.sample(150)

        # project to meters
        candidates["x"], candidates["y"] = zip(*candidates.geometry.apply(
            lambda g: project(g.x, g.y)
        ))

        points_xy = candidates[["x", "y"]].to_numpy()

        selected, assignments, obj = solve_p_median(points_xy, p)

        lamps = assign_lamp_types(
            selected,
            points_xy,
            assignments,
            lamp_types
        )

        result = []
        for lamp in lamps:
            row = candidates.iloc[lamp["index"]]
            result.append({
                "lat": row.geometry.y,
                "lon": row.geometry.x,
                "lamp_type": lamp["lamp_type"],
                "radius": lamp["radius"],
                "cost": lamp["cost"]
            })

        return {
            "lamps": result,
            "objective_value": obj
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
