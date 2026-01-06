from fastapi import APIRouter, HTTPException
import numpy as np
import pyproj
import geopandas as gpd
from app.core.osm import fetch_roads_from_polygon
from app.core.sampling import sample_points_on_roads
from app.core.geometry import validate_polygon
from app.optimization.solver import solve_streetlight_coverage
from ortools.sat.python import cp_model

router = APIRouter()

# Global projector to avoid initialization noise and ensure consistency
PROJECTOR = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform

@router.post("/optimize")
def optimize(payload: dict):
    try:
        poly_coords = payload.get("polygon")
        polygon = validate_polygon(poly_coords)
        options = payload.get("options", {})
        max_budget = float(options.get("max_budget", 0))
        
        # 1. Fetch Roads
        roads_gdf = fetch_roads_from_polygon(polygon)
        if roads_gdf.empty:
            raise HTTPException(status_code=400, detail="No roads found in the selected area.")
        
        # 2. CRITICAL FIX: Clean and Deduplicate Road Geometry
        # This prevents the 'False 100%' error by merging overlapping road segments
        # before we start sampling demand 'pieces'.
        roads_gdf = roads_gdf.dissolve() 
        roads_gdf = roads_gdf.explode(index_parts=False).reset_index(drop=True)
        
        # Sort by geometry to maintain deterministic point generation
        roads_gdf = roads_gdf.sort_values(by=['geometry']).reset_index(drop=True)
        
        # 3. Sampling Logic
        # J: Candidates (Every 25m) - sparse for solver performance
        # I: Demand Pieces (Every 3m) - dense for visual accuracy
        CANDIDATE_SPACING = 25
        DEMAND_SPACING = 3
        
        j_gdf = sample_points_on_roads(roads_gdf, spacing=CANDIDATE_SPACING)
        i_gdf = sample_points_on_roads(roads_gdf, spacing=DEMAND_SPACING)

        # 4. Safety Check for empty results
        if j_gdf.empty or i_gdf.empty:
            raise HTTPException(
                status_code=400, 
                detail="The selected area is too small for sampling. Try a larger area."
            )
        
        # 5. Project to Meters & Rounding for numerical stability
        j_meters = np.array([PROJECTOR(p.x, p.y) for p in j_gdf.geometry if not p.is_empty])
        i_meters = np.array([PROJECTOR(p.x, p.y) for p in i_gdf.geometry if not p.is_empty])
        
        j_meters = np.round(j_meters, 3)
        i_meters = np.round(i_meters, 3)

        if len(j_meters) == 0 or len(i_meters) == 0:
            raise HTTPException(status_code=400, detail="Coordinate projection failed.")

        # 6. Run Solver
        lamp_types = payload.get("lamp_types", [])
        # Ensure lamp types are processed in a consistent order
        lamp_types = sorted(lamp_types, key=lambda k: k.get('name', ''))
        
        solver, x, y, status = solve_streetlight_coverage(
            j_meters, i_meters, lamp_types, max_budget
        )

        # 7. Parse Results
        results = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for j in range(len(j_meters)):
                for l_idx, lt in enumerate(lamp_types):
                    if solver.Value(x[j, l_idx]) == 1:
                        point = j_gdf.iloc[j].geometry
                        results.append({
                            "lat": point.y, 
                            "lon": point.x,
                            "lamp_type": lt.get("name"),
                            "radius": lt.get("radius"),
                            "cost": lt.get("cost"),
                            "color": lt.get("color")
                        })

        # 8. Calculate Metrics
        total_pieces = len(i_meters)
        covered_pieces = sum(solver.Value(y_var) for y_var in y)
        coverage_pct = (covered_pieces / total_pieces) * 100 if total_pieces > 0 else 0
        
        # Correctly estimate length based on the 3m piece spacing
        estimated_coverage_m = covered_pieces * DEMAND_SPACING 

        return {
            "lamps": results,
            "coverage_pct": round(coverage_pct, 2),
            "coverage_length_m": round(estimated_coverage_m, 2),
            "total_cost": round(sum(l['cost'] for l in results), 2),
            "status": solver.StatusName(status),
            "points_covered": covered_pieces,
            "total_points": total_pieces
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))