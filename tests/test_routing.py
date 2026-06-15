"""Tests for Dijkstra least-latency routing."""

from constellation_sim.routing import shortest_path


def test_simple_shortest_path():
    graph = {
        "A": {"B": 1.0, "C": 4.0},
        "B": {"A": 1.0, "C": 1.0, "D": 5.0},
        "C": {"A": 4.0, "B": 1.0, "D": 1.0},
        "D": {"B": 5.0, "C": 1.0},
    }
    route = shortest_path(graph, "A", "D")
    assert route.path == ["A", "B", "C", "D"]
    assert route.total_delay_s == 3.0
    assert route.hop_count == 3


def test_source_equals_target():
    graph = {"A": {"B": 1.0}, "B": {"A": 1.0}}
    route = shortest_path(graph, "A", "A")
    assert route.path == ["A"]
    assert route.total_delay_s == 0.0
    assert route.hop_count == 0


def test_unreachable_target():
    graph = {"A": {"B": 1.0}, "B": {"A": 1.0}, "C": {}}
    route = shortest_path(graph, "A", "C")
    assert not route.is_connected
    assert route.total_delay_s == float("inf")


def test_missing_node():
    graph = {"A": {"B": 1.0}, "B": {"A": 1.0}}
    route = shortest_path(graph, "A", "Z")
    assert not route.is_connected


def test_prefers_lower_total_delay_over_fewer_hops():
    # A->D direct is 10; A->B->C->D is 3 via three hops. Latency wins.
    graph = {
        "A": {"D": 10.0, "B": 1.0},
        "B": {"A": 1.0, "C": 1.0},
        "C": {"B": 1.0, "D": 1.0},
        "D": {"A": 10.0, "C": 1.0},
    }
    route = shortest_path(graph, "A", "D")
    assert route.path == ["A", "B", "C", "D"]
    assert route.total_delay_s == 3.0
