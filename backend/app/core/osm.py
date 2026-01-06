import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon

def fetch_roads_from_polygon(
    polygon: Polygon,
    network_type: str = "drive"
) -> gpd.GeoDataFrame:
    """
    Downloads OSM road network within the provided polygon.
    """
    try:
        graph = ox.graph_from_polygon(
            polygon,
            network_type=network_type,
            simplify=True,
            retain_all=True
        )
    except Exception:
        raise ValueError("The selected area contains no road data.")

    # Convert graph to GeoDataFrame
    # ox returns (nodes, edges)
    _, edges = ox.graph_to_gdfs(graph)

    if edges.empty:
        raise ValueError("No roads found in the selected polygon.")

    # Select only necessary columns
    needed_cols = ["geometry", "highway", "length"]
    # OSMnx columns vary; ensure they exist
    existing_cols = [c for c in needed_cols if c in edges.columns]
    
    edges = edges[existing_cols].copy()
    edges.reset_index(drop=True, inplace=True)
    
    return edges