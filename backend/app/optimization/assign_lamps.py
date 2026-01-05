import numpy as np


def assign_lamp_types(
    facility_indices,
    points_xy,
    assignments,
    lamp_types
):
    """
    Assign cheapest feasible lamp to each facility.
    """

    lamps = []

    for j in facility_indices:
        assigned_points = points_xy[assignments == j]

        if len(assigned_points) == 0:
            required_radius = 0
        else:
            required_radius = np.max(
                np.linalg.norm(assigned_points - points_xy[j], axis=1)
            )

        feasible = [
            l for l in lamp_types
            if l["radius"] >= required_radius
        ]

        if not feasible:
            # fallback: pick largest radius lamp
            chosen = max(lamp_types, key=lambda l: l["radius"])
        else:
            chosen = min(feasible, key=lambda l: l["cost"])


        lamps.append({
            "index": j,
            "lamp_type": chosen["id"],
            "radius": chosen["radius"],
            "cost": chosen["cost"]
        })

    return lamps
