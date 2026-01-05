from shapely.geometry import Polygon
from shapely.ops import transform
from pyproj import CRS, Transformer


def validate_polygon(coords: list[list[float]]) -> Polygon:
    """
    coords: [[lon, lat], ...]
    returns: valid Shapely Polygon (WGS84)
    """
    if len(coords) < 3:
        raise ValueError("Polygon must have at least 3 points")

    # Ensure polygon is closed
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]

    poly = Polygon(coords)

    if not poly.is_valid:
        raise ValueError("Invalid polygon geometry")

    if poly.area == 0:
        raise ValueError("Polygon area is zero")

    return poly


def polygon_to_bbox(polygon: Polygon) -> tuple[float, float, float, float]:
    """
    Returns (north, south, east, west) in lat/lon
    """
    minx, miny, maxx, maxy = polygon.bounds
    return maxy, miny, maxx, minx


def project_to_utm(geometry: Polygon):
    """
    Projects geometry from WGS84 to appropriate UTM zone
    Returns (projected_geometry, transformer_back)
    """
    lon, lat = geometry.centroid.x, geometry.centroid.y
    utm_crs = CRS.from_user_input(
        CRS.from_epsg(4326).utm_zone(lon, lat)
    )

    to_utm = Transformer.from_crs("EPSG:4326", utm_crs, always_xy=True).transform
    to_wgs = Transformer.from_crs(utm_crs, "EPSG:4326", always_xy=True).transform

    projected = transform(to_utm, geometry)
    return projected, to_wgs
