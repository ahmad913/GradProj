from ortools.sat.python import cp_model
import numpy as np

def solve_streetlight_coverage(
    cand_coords: np.ndarray, 
    dem_coords: np.ndarray, 
    lamp_types: list, 
    max_budget: float
):
    model = cp_model.CpModel()
    num_j = len(cand_coords)
    num_i = len(dem_coords)
    
    # --- SPEED OPTIMIZATION: Vectorized Distance Matrix ---
    # We do the heavy math in one shot using NumPy
    diff = cand_coords[:, np.newaxis, :] - dem_coords[np.newaxis, :, :]
    dist_matrix = np.round(np.sqrt((diff ** 2).sum(axis=2)), 2)

    # --- VARIABLES ---
    x = {}
    for j in range(num_j):
        for l in range(len(lamp_types)):
            x[j, l] = model.NewBoolVar(f'x_{j}_{l}')
    y = [model.NewBoolVar(f'y_{i}') for i in range(num_i)]

    # --- 1. BUDGET CONSTRAINT ---
    SCALE = 100
    costs = [int(round(lt['cost'] * SCALE)) for lt in lamp_types]
    total_cost_expr = sum(x[j, l] * costs[l] for j in range(num_j) for l in range(len(lamp_types)))
    model.Add(total_cost_expr <= int(round(max_budget * SCALE)))

    # --- 2. DYNAMIC SPACING CONSTRAINT (OPTIMIZED) ---
    # Lamps shouldn't overlap their 'cores'. 
    # Logic: Dist(j1, j2) must be >= (Radius_L1 + Radius_L2) * 0.6
    # We only add constraints for candidates that are actually close to save time.
    for j1 in range(num_j):
        for j2 in range(j1 + 1, num_j):
            d_j1_j2 = np.linalg.norm(cand_coords[j1] - cand_coords[j2])
            
            for l1_idx, lt1 in enumerate(lamp_types):
                for l2_idx, lt2 in enumerate(lamp_types):
                    min_allowed = (lt1['radius'] + lt2['radius']) * 0.6
                    if d_j1_j2 < min_allowed:
                        # If they are too close, they cannot both be active
                        model.Add(x[j1, l1_idx] + x[j2, l2_idx] <= 1)

    # --- 3. COVERAGE LOGIC (PRE-FILTERED) ---
    for i in range(num_i):
        # We pre-calculate which (j, l) can cover point i
        # This is much faster than letting the solver figure it out
        covering_options = []
        for l_idx, lt in enumerate(lamp_types):
            # Find indices of candidates that are within range
            reachable_j = np.where(dist_matrix[:, i] <= lt['radius'])[0]
            for j in reachable_j:
                covering_options.append(x[j, l_idx])
        
        if covering_options:
            model.Add(y[i] <= sum(covering_options))
        else:
            model.Add(y[i] == 0)

    # --- 4. MULTI-OBJECTIVE ---
    # We use a smaller coverage weight to keep the numbers within 64-bit integer limits
    coverage_weight = 10_000 
    model.Maximize(sum(y) * coverage_weight - total_cost_expr)

    # --- SOLVER ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0 # Increased for higher precision
    solver.parameters.num_search_workers = 4 # Enable multi-threading for speed
    status = solver.Solve(model)

    return solver, x, y, status