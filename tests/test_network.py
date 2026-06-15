"""Tests for link geometry and graph construction."""

import numpy as np

from constellation_sim.constants import EARTH_RADIUS_KM
from constellation_sim.network import (
    GroundNode,
    build_network_graph,
    elevation_angle_deg,
    has_line_of_sight,
    is_visible,
)
from constellation_sim.orbits import geodetic_to_ecef
from constellation_sim.constellation import walker_delta


def test_line_of_sight_blocked_by_earth():
    # Two points on opposite sides of the Earth at the surface cannot see each
    # other; the chord passes through the planet.
    p1 = np.array([EARTH_RADIUS_KM, 0.0, 0.0])
    p2 = np.array([-EARTH_RADIUS_KM, 0.0, 0.0])
    assert not has_line_of_sight(p1, p2)


def test_line_of_sight_clear_for_high_satellites():
    # Two satellites high above adjacent points keep line of sight.
    p1 = np.array([EARTH_RADIUS_KM + 550.0, 100.0, 0.0])
    p2 = np.array([EARTH_RADIUS_KM + 550.0, -100.0, 0.0])
    assert has_line_of_sight(p1, p2)


def test_elevation_directly_overhead_is_90():
    ground = geodetic_to_ecef(0.0, 0.0, 0.0)
    overhead = geodetic_to_ecef(0.0, 0.0, 550.0)
    assert elevation_angle_deg(ground, overhead) > 89.0


def test_satellite_below_horizon_not_visible():
    ground = geodetic_to_ecef(0.0, 0.0, 0.0)
    # A point on the far side of the Earth is well below the horizon.
    far = geodetic_to_ecef(0.0, 180.0, 550.0)
    assert not is_visible(ground, far)


def test_build_graph_is_symmetric_and_nonnegative():
    sats = walker_delta(num_planes=6, sats_per_plane=6, inclination_deg=53.0, altitude_km=550.0)
    ground = [GroundNode("A", 0.0, 0.0), GroundNode("B", 10.0, 20.0)]
    graph = build_network_graph(sats, ground, t=0.0)

    for u, nbrs in graph.items():
        for v, w in nbrs.items():
            assert w >= 0.0
            assert graph[v][u] == w  # undirected / symmetric delays


def test_all_nodes_present_in_graph():
    sats = walker_delta(num_planes=4, sats_per_plane=4, inclination_deg=53.0, altitude_km=550.0)
    ground = [GroundNode("A", 0.0, 0.0)]
    graph = build_network_graph(sats, ground, t=0.0)
    assert "A" in graph
    for s in sats:
        assert s.sat_id in graph
