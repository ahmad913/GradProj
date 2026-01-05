import numpy as np
from ortools.linear_solver import pywraplp


def solve_p_median(
    points: np.ndarray,
    p: int,
    time_limit_sec: int = 30
):
    """
    Solve Euclidean p-median.
    
    Parameters
    ----------
    points : np.ndarray (N, 2)
        Candidate coordinates in meters (EPSG:3857)
    p : int
        Number of facilities
    time_limit_sec : int
        Solver time limit
    
    Returns
    -------
    selected_indices : list[int]
        Indices of selected facility locations
    objective_value : float
        Total distance
    """

    n = points.shape[0]

    if p <= 0 or p > n:
        raise ValueError("p must be between 1 and number of points")

    # Distance matrix
    dist = np.linalg.norm(
        points[:, None, :] - points[None, :, :],
        axis=2
    )

    solver = pywraplp.Solver.CreateSolver("CBC")
    if solver is None:
        raise RuntimeError("CBC solver not available")

    solver.SetTimeLimit(time_limit_sec * 1000)

    # Variables
    x = {}
    y = {}

    for i in range(n):
        y[i] = solver.BoolVar(f"y[{i}]")
        for j in range(n):
            x[i, j] = solver.BoolVar(f"x[{i},{j}]")

    # Objective
    solver.Minimize(
        solver.Sum(dist[i, j] * x[i, j] for i in range(n) for j in range(n))
    )

    # Each demand assigned to exactly one facility
    for i in range(n):
        solver.Add(
            solver.Sum(x[i, j] for j in range(n)) == 1
        )

    # Assignment only to open facilities
    for i in range(n):
        for j in range(n):
            solver.Add(x[i, j] <= y[j])

    # Exactly p facilities
    solver.Add(
        solver.Sum(y[j] for j in range(n)) == p
    )

    status = solver.Solve()

    if status not in (
        pywraplp.Solver.OPTIMAL,
        pywraplp.Solver.FEASIBLE
    ):
        raise RuntimeError("p-median solver failed")

    selected = [j for j in range(n) if y[j].solution_value() > 0.5]

    assignments = np.zeros(n, dtype=int)

    for i in range(n):
        for j in range(n):
            if x[i, j].solution_value() > 0.5:
                assignments[i] = j

    return selected, assignments, solver.Objective().Value()
