import geopandas as gpd
from shapely.geometry import LineString, Point
import numpy as np


def sample_points_on_roads(
    roads: gpd.GeoDataFrame,
    spacing: float = 30
) -> gpd.GeoDataFrame:
    """
    Sample points every `spacing` meters along road geometries.
    Assumes geometry is in EPSG:4326, spacing is approximated in degrees.
    """

    points = []

    for geom in roads.geometry:
        if geom is None:
            continue

        if geom.geom_type == "MultiLineString":
            lines = geom.geoms
        elif geom.geom_type == "LineString":
            lines = [geom]
        else:
            continue

        for line in lines:
            length = line.length
            if length == 0:
                continue

            num_points = max(int(length / spacing), 1)

            for i in range(num_points + 1):
                point = line.interpolate(i / num_points, normalized=True)
                points.append(point)

    if not points:
        raise ValueError("No candidate points generated")

    return gpd.GeoDataFrame(
        geometry=points,
        crs=roads.crs
    )
