"""Link geometry and live network-graph construction.

At each instant the constellation plus the ground terminals form a graph:

- **Nodes** are satellites and ground nodes.
- **Edges** are usable links, weighted by one-way propagation delay
  (``distance / c``), which is what dominates real Starlink latency.

Two link types are modelled:

1. **Up/downlinks** between a ground node and a satellite, gated by a minimum
   elevation angle (the satellite must be high enough above the horizon).
2. **Inter-satellite laser links (ISLs)** between satellites, using a ``+grid``
   topology — each satellite links to its in-plane neighbours (ahead/behind)
   and to the nearest satellites in the adjacent planes — subject to a maximum
   range and an unobstructed line of sight past the Earth.

All geometry is done in the rotating ECEF frame so ground nodes are stationary.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .constants import (
    DEFAULT_GROUND_ALTITUDE_KM,
    DEFAULT_MIN_ELEVATION_DEG,
    EARTH_RADIUS_KM,
    SPEED_OF_LIGHT_KMS,
)
from .constellation import Satellite
from .orbits import geodetic_to_ecef


@dataclass(frozen=True)
class GroundNode:
    """A fixed terminal on the Earth's surface (user, gateway, or PoP)."""

    name: str
    lat_deg: float
    lon_deg: float
    alt_km: float = DEFAULT_GROUND_ALTITUDE_KM

    def position_ecef(self, t: float = 0.0) -> np.ndarray:
        # Stationary in ECEF, so the timestamp is irrelevant.
        return geodetic_to_ecef(self.lat_deg, self.lon_deg, self.alt_km)


def propagation_delay_s(p1: np.ndarray, p2: np.ndarray) -> float:
    """One-way light-speed delay (s) between two ECEF points (km)."""
    return float(np.linalg.norm(p1 - p2)) / SPEED_OF_LIGHT_KMS


def has_line_of_sight(p1: np.ndarray, p2: np.ndarray, body_radius_km: float = EARTH_RADIUS_KM) -> bool:
    """Return True if the segment p1->p2 is not blocked by the Earth.

    We find the closest approach of the infinite line to the Earth's centre. If
    that closest point lies *between* the endpoints and is below the surface,
    the Earth occludes the link.
    """
    d = p2 - p1
    d_norm_sq = float(np.dot(d, d))
    if d_norm_sq == 0.0:
        return True

    # Parameter of the closest point to the origin along the segment.
    s = -float(np.dot(p1, d)) / d_norm_sq
    if s <= 0.0 or s >= 1.0:
        # Closest approach is outside the segment; endpoints face each other.
        return True

    closest = p1 + s * d
    return float(np.linalg.norm(closest)) >= body_radius_km


def elevation_angle_deg(ground_ecef: np.ndarray, sat_ecef: np.ndarray) -> float:
    """Elevation of the satellite above the ground node's local horizon (deg)."""
    up = ground_ecef / np.linalg.norm(ground_ecef)  # local vertical
    to_sat = sat_ecef - ground_ecef
    to_sat_norm = np.linalg.norm(to_sat)
    if to_sat_norm == 0.0:
        return 90.0
    sin_elev = float(np.dot(to_sat, up) / to_sat_norm)
    sin_elev = max(-1.0, min(1.0, sin_elev))
    return math.degrees(math.asin(sin_elev))


def is_visible(
    ground_ecef: np.ndarray,
    sat_ecef: np.ndarray,
    min_elevation_deg: float = DEFAULT_MIN_ELEVATION_DEG,
) -> bool:
    """Whether a ground node can use a satellite (elevation gate)."""
    return elevation_angle_deg(ground_ecef, sat_ecef) >= min_elevation_deg


def _isl_neighbors(satellites: list[Satellite]) -> set[tuple[int, int]]:
    """Index pairs that form the static ``+grid`` ISL pattern.

    Connectivity follows plane/slot adjacency, not live geometry; the geometric
    feasibility (range + line of sight) is checked later at graph-build time.
    """
    by_plane: dict[int, list[int]] = {}
    for idx, sat in enumerate(satellites):
        by_plane.setdefault(sat.plane, []).append(idx)
    for idxs in by_plane.values():
        idxs.sort(key=lambda i: satellites[i].slot)

    planes = sorted(by_plane.keys())
    edges: set[tuple[int, int]] = set()

    # In-plane: ring of ahead/behind neighbours.
    for idxs in by_plane.values():
        n = len(idxs)
        for k in range(n):
            a, b = idxs[k], idxs[(k + 1) % n]
            edges.add((min(a, b), max(a, b)))

    # Cross-plane: same slot in the next plane (wrapping around).
    for pi, plane in enumerate(planes):
        next_plane = planes[(pi + 1) % len(planes)]
        cur = {satellites[i].slot: i for i in by_plane[plane]}
        nxt = {satellites[i].slot: i for i in by_plane[next_plane]}
        for slot, i in cur.items():
            if slot in nxt:
                a, b = i, nxt[slot]
                if a != b:
                    edges.add((min(a, b), max(a, b)))

    return edges


def build_network_graph(
    satellites: list[Satellite],
    ground_nodes: list[GroundNode],
    t: float,
    min_elevation_deg: float = DEFAULT_MIN_ELEVATION_DEG,
    max_isl_range_km: float = 5000.0,
) -> dict[str, dict[str, float]]:
    """Build the weighted adjacency graph at time ``t``.

    Returns
    -------
    dict
        ``graph[node][neighbor] = one_way_delay_seconds``. Node keys are
        satellite ids and ground-node names.

    Parameters
    ----------
    max_isl_range_km:
        Maximum laser-link range. Pairs farther apart, or with the Earth in the
        way, are dropped even if they are topological neighbours.
    """
    # Cache positions once per call.
    sat_pos = [sat.position_ecef(t) for sat in satellites]
    ground_pos = {g.name: g.position_ecef(t) for g in ground_nodes}

    graph: dict[str, dict[str, float]] = {sat.sat_id: {} for sat in satellites}
    for g in ground_nodes:
        graph[g.name] = {}

    def add_edge(a: str, b: str, delay: float) -> None:
        graph[a][b] = delay
        graph[b][a] = delay

    # Inter-satellite links.
    for i, j in _isl_neighbors(satellites):
        pi, pj = sat_pos[i], sat_pos[j]
        if np.linalg.norm(pi - pj) > max_isl_range_km:
            continue
        if not has_line_of_sight(pi, pj):
            continue
        add_edge(satellites[i].sat_id, satellites[j].sat_id, propagation_delay_s(pi, pj))

    # Ground up/downlinks.
    for g in ground_nodes:
        gp = ground_pos[g.name]
        for sat, sp in zip(satellites, sat_pos):
            if is_visible(gp, sp, min_elevation_deg):
                add_edge(g.name, sat.sat_id, propagation_delay_s(gp, sp))

    return graph
