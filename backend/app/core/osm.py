import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon


def fetch_roads_from_polygon(
    polygon: Polygon,
    network_type: str = "drive"
) -> gpd.GeoDataFrame:

    graph = ox.graph_from_polygon(
        polygon,
        network_type=network_type,
        simplify=True
    )

    gdfs = ox.graph_to_gdfs(graph)

    # gdfs may be tuple or single gdf depending on version
    if isinstance(gdfs, tuple):
        edges = gdfs[1]
    else:
        edges = gdfs

    if edges.empty:
        raise ValueError("No roads found in selected area")

    edges = edges[[
        "geometry",
        "osmid",
        "highway",
        "length"
    ]].copy()

    edges.rename(columns={
        "osmid": "osm_id",
        "length": "length_m"
    }, inplace=True)

    edges.reset_index(drop=True, inplace=True)
    edges["id"] = edges.index.astype(str)

    return edges
