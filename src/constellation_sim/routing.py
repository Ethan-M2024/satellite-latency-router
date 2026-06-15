"""Least-latency routing over the live network graph.

Given the weighted adjacency graph produced by
:func:`~constellation_sim.network.build_network_graph`, we find the minimum
total-delay path from a source node to a destination node using Dijkstra's
algorithm with a binary heap. Edge weights are one-way propagation delays, so
the path cost is the end-to-end propagation latency.
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass


@dataclass(frozen=True)
class Route:
    """A computed path and its cost."""

    path: list[str]
    """Ordered list of node ids from source to destination (empty if none)."""
    total_delay_s: float
    """Sum of edge delays along the path (inf if unreachable)."""

    @property
    def hop_count(self) -> int:
        """Number of links traversed (0 if no path)."""
        return max(0, len(self.path) - 1)

    @property
    def is_connected(self) -> bool:
        return len(self.path) > 0


def shortest_path(
    graph: dict[str, dict[str, float]],
    source: str,
    target: str,
) -> Route:
    """Dijkstra shortest path by total delay.

    Parameters
    ----------
    graph:
        ``graph[u][v] = delay`` adjacency mapping with non-negative weights.
    source, target:
        Node ids present in ``graph``.

    Returns
    -------
    Route
        The minimum-delay path, or an empty route with ``inf`` delay if the
        target is unreachable.
    """
    if source not in graph or target not in graph:
        return Route(path=[], total_delay_s=float("inf"))
    if source == target:
        return Route(path=[source], total_delay_s=0.0)

    dist: dict[str, float] = {source: 0.0}
    prev: dict[str, str] = {}
    visited: set[str] = set()
    heap: list[tuple[float, str]] = [(0.0, source)]

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == target:
            break
        for v, w in graph[u].items():
            if v in visited:
                continue
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    if target not in dist:
        return Route(path=[], total_delay_s=float("inf"))

    # Reconstruct the path back to the source.
    path = [target]
    while path[-1] != source:
        path.append(prev[path[-1]])
    path.reverse()
    return Route(path=path, total_delay_s=dist[target])
