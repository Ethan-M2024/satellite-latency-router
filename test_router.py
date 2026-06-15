"""Tests for satellite_router.py. Run with: pytest"""

import math

from satellite_router import (
    build_demo_network,
    build_graph,
    distance_km,
    latency_ms,
    shortest_path,
    to_xyz,
)


def test_distance_to_self_is_zero():
    p = to_xyz(47.6, -122.3, 0.0)
    assert distance_km(p, p) == 0.0


def test_higher_altitude_is_farther_from_center():
    ground = to_xyz(0.0, 0.0, 0.0)
    satellite = to_xyz(0.0, 0.0, 550.0)
    center = (0.0, 0.0, 0.0)
    assert distance_km(satellite, center) > distance_km(ground, center)


def test_latency_grows_with_distance():
    assert latency_ms(1000.0) < latency_ms(2000.0)
    # Light covers 299,792 km in exactly 1000 ms.
    assert latency_ms(299792.458) == 1000.0


def test_dijkstra_finds_lowest_total_latency():
    # Direct A->C is slow (10); going A->B->C is faster (2). Latency should win.
    graph = {
        "A": {"C": 10.0, "B": 1.0},
        "B": {"A": 1.0, "C": 1.0},
        "C": {"A": 10.0, "B": 1.0},
    }
    path, total = shortest_path(graph, "A", "C")
    assert path == ["A", "B", "C"]
    assert total == 2.0


def test_no_path_returns_empty():
    graph = {"A": {}, "B": {}}
    path, total = shortest_path(graph, "A", "B")
    assert path == []
    assert total == math.inf


def test_demo_routes_seattle_to_london():
    graph = build_graph(build_demo_network())
    path, one_way = shortest_path(graph, "Seattle", "London")

    assert path[0] == "Seattle"
    assert path[-1] == "London"
    # Traffic must hop through satellites, not go city-to-city directly.
    assert len(path) > 2
    assert all("SAT" in node for node in path[1:-1])
    # LEO latency should be well under terrestrial fiber (~65 ms RTT here).
    assert one_way < 75.0


def test_cities_never_link_directly():
    graph = build_graph(build_demo_network())
    assert "London" not in graph["Seattle"]
