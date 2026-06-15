"""
satellite_router.py
===================

A small simulation of how Starlink-style satellites route internet traffic.

The idea: a city can't always reach another city directly over satellites, so
traffic "hops" from one satellite to the next until it can come back down near
the destination. Each hop adds a little delay (signals travel at the speed of
light). This program builds a small network of satellites and ground cities,
then finds the path with the *lowest total latency* using Dijkstra's algorithm.

Run it:
    python satellite_router.py

Only uses the Python standard library.
"""

from __future__ import annotations

import heapq
import math

# --- Physical constants -----------------------------------------------------

EARTH_RADIUS_KM = 6371.0
SPEED_OF_LIGHT_KMS = 299_792.458   # signals travel ~at the speed of light
SAT_ALTITUDE_KM = 550.0            # typical Starlink altitude

# A satellite can talk to another satellite only if they are within this range.
MAX_SAT_LINK_KM = 3000.0
# A city can use a satellite only if the satellite is within this range overhead.
MAX_GROUND_LINK_KM = 2000.0


# --- Geometry helpers -------------------------------------------------------

def to_xyz(lat_deg: float, lon_deg: float, altitude_km: float) -> tuple[float, float, float]:
    """Turn latitude/longitude/altitude into 3D coordinates (km).

    We treat the Earth as a sphere. This lets us measure the straight-line
    distance between any two points (cities or satellites) in space.
    """
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    r = EARTH_RADIUS_KM + altitude_km
    x = r * math.cos(lat) * math.cos(lon)
    y = r * math.cos(lat) * math.sin(lon)
    z = r * math.sin(lat)
    return (x, y, z)


def distance_km(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    """Straight-line distance between two 3D points (km)."""
    return math.dist(a, b)


def latency_ms(distance: float) -> float:
    """One-way time for a signal to cross this distance (milliseconds)."""
    return distance / SPEED_OF_LIGHT_KMS * 1000.0


# --- Network model ----------------------------------------------------------

class Node:
    """A point in the network: either a satellite or a ground city."""

    def __init__(self, name: str, lat: float, lon: float, altitude_km: float):
        self.name = name
        self.pos = to_xyz(lat, lon, altitude_km)
        self.is_satellite = altitude_km > 0


def build_graph(nodes: list[Node]) -> dict[str, dict[str, float]]:
    """Connect the nodes into a network and weight each link by its latency.

    Rules:
      * satellite <-> satellite : connect if within MAX_SAT_LINK_KM
      * city      <-> satellite : connect if within MAX_GROUND_LINK_KM
      * city      <-> city      : never directly (must go through satellites)
    """
    graph: dict[str, dict[str, float]] = {n.name: {} for n in nodes}

    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            both_ground = not a.is_satellite and not b.is_satellite
            if both_ground:
                continue  # cities never talk to each other directly

            limit = MAX_SAT_LINK_KM if (a.is_satellite and b.is_satellite) else MAX_GROUND_LINK_KM
            dist = distance_km(a.pos, b.pos)
            if dist <= limit:
                weight = latency_ms(dist)
                graph[a.name][b.name] = weight
                graph[b.name][a.name] = weight

    return graph


# --- Routing ----------------------------------------------------------------

def shortest_path(
    graph: dict[str, dict[str, float]], start: str, end: str
) -> tuple[list[str], float]:
    """Find the lowest-latency path from start to end (Dijkstra's algorithm).

    Returns the list of nodes in the path and the total one-way latency (ms).
    If there is no path, returns ([], infinity).
    """
    best_time = {start: 0.0}
    came_from: dict[str, str] = {}
    visited: set[str] = set()
    queue = [(0.0, start)]  # (time so far, node)

    while queue:
        time_so_far, node = heapq.heappop(queue)
        if node in visited:
            continue
        visited.add(node)
        if node == end:
            break

        for neighbor, link_time in graph[node].items():
            if neighbor in visited:
                continue
            new_time = time_so_far + link_time
            if new_time < best_time.get(neighbor, math.inf):
                best_time[neighbor] = new_time
                came_from[neighbor] = node
                heapq.heappush(queue, (new_time, neighbor))

    if end not in best_time:
        return ([], math.inf)

    # Walk backwards from the end to rebuild the path.
    path = [end]
    while path[-1] != start:
        path.append(came_from[path[-1]])
    path.reverse()
    return (path, best_time[end])


# --- Demo -------------------------------------------------------------------

def build_demo_network() -> list[Node]:
    """A grid of satellites over the North Atlantic, plus two cities."""
    nodes: list[Node] = []

    # 2 rows x 6 columns of satellites spanning Seattle -> London.
    for lat in (45.0, 58.0):
        for lon in range(-125, 16, 28):  # -125, -97, -69, -41, -13, 15
            nodes.append(Node(f"SAT({lat:.0f},{lon})", lat, float(lon), SAT_ALTITUDE_KM))

    # Ground cities (altitude 0).
    nodes.append(Node("Seattle", 47.61, -122.33, 0.0))
    nodes.append(Node("London", 51.51, -0.13, 0.0))

    return nodes


def main() -> None:
    nodes = build_demo_network()
    graph = build_graph(nodes)

    start, end = "Seattle", "London"
    path, one_way = shortest_path(graph, start, end)

    print(f"Routing internet traffic: {start} -> {end}\n")
    if not path:
        print("No route found. Try increasing the link ranges.")
        return

    print("Lowest-latency path:")
    for hop in path:
        print(f"   {hop}")

    hops = len(path) - 1
    print(f"\nSatellite hops : {hops}")
    print(f"One-way latency: {one_way:.1f} ms")
    print(f"Round-trip (RTT): {2 * one_way:.1f} ms")
    print("\n(For comparison, fiber Seattle<->London is ~130-140 ms RTT.)")


if __name__ == "__main__":
    main()
