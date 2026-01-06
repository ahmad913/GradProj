import geopandas as gpd
from shapely.geometry import LineString, Point
import numpy as np

def sample_points_on_roads(
    roads: gpd.GeoDataFrame,
    spacing: float = 30
) -> gpd.GeoDataFrame:
    """
    Sample points every `spacing` meters along road geometries.
    Ensures math is done in a metric CRS (EPSG:3857) for accuracy.
    """
    # 1. Temporarily project to meters to do accurate linear sampling
    original_crs = roads.crs
    roads_m = roads.to_crs("EPSG:3857")
    
    points = []
    for geom in roads_m.geometry:
        if geom is None or geom.is_empty:
            continue

        # Handle both LineString and MultiLineString
        lines = geom.geoms if geom.geom_type == "MultiLineString" else [geom]

        for line in lines:
            # Calculate distance-based sampling
            length = line.length
            if length < spacing and length > 0:
                points.append(line.interpolate(length / 2))
                continue
            
            if length == 0:
                continue
            
            # Generate distances from 0 to length
            distances = np.arange(0, length, spacing)
            for dist in distances:
                points.append(line.interpolate(dist))
            
            # Always ensure the very end of the line is included as a candidate
            points.append(line.interpolate(length))

    if not points:
        raise ValueError("No road points could be sampled in this area.")

    # 2. Create GDF in meters, then convert back to original CRS (Lat/Lon)
    gdf_m = gpd.GeoDataFrame(geometry=points, crs="EPSG:3857")
    return gdf_m.to_crs(original_crs)