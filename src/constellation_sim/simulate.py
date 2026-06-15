"""Time-stepped simulation driver.

Walks the constellation forward in fixed steps. At each step it rebuilds the
network graph (because the satellites have moved) and recomputes the
least-latency route between a source and destination ground node. The result is
a timeseries that the metrics and visualization modules consume.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .constants import DEFAULT_MIN_ELEVATION_DEG
from .constellation import Satellite
from .network import GroundNode, build_network_graph
from .routing import Route, shortest_path


@dataclass
class SimulationResult:
    """The output of a run: aligned per-timestep arrays."""

    times_s: list[float] = field(default_factory=list)
    routes: list[Route] = field(default_factory=list)
    source: str = ""
    target: str = ""

    @property
    def latencies_ms(self) -> list[float]:
        """Round-trip latency estimate per step (ms).

        Propagation is symmetric, so RTT ~= 2 * one-way delay. Unreachable
        steps are reported as ``inf``.
        """
        out = []
        for r in self.routes:
            out.append(float("inf") if not r.is_connected else 2.0 * r.total_delay_s * 1000.0)
        return out

    @property
    def hop_counts(self) -> list[int]:
        return [r.hop_count for r in self.routes]


def run_simulation(
    satellites: list[Satellite],
    ground_nodes: list[GroundNode],
    source: str,
    target: str,
    duration_s: float,
    step_s: float,
    min_elevation_deg: float = DEFAULT_MIN_ELEVATION_DEG,
    max_isl_range_km: float = 5000.0,
) -> SimulationResult:
    """Run the constellation forward and route ``source`` -> ``target``.

    Parameters
    ----------
    satellites:
        The constellation (e.g. from :func:`constellation.walker_delta`).
    ground_nodes:
        All terminals; ``source`` and ``target`` must be among their names.
    duration_s, step_s:
        Total simulated time and the timestep, both in seconds.

    Returns
    -------
    SimulationResult
        Per-step times, routes, and derived latency/hop arrays.
    """
    names = {g.name for g in ground_nodes}
    for endpoint in (source, target):
        if endpoint not in names:
            raise ValueError(f"endpoint {endpoint!r} is not a known ground node")

    result = SimulationResult(source=source, target=target)

    t = 0.0
    while t <= duration_s + 1e-9:
        graph = build_network_graph(
            satellites,
            ground_nodes,
            t=t,
            min_elevation_deg=min_elevation_deg,
            max_isl_range_km=max_isl_range_km,
        )
        result.times_s.append(t)
        result.routes.append(shortest_path(graph, source, target))
        t += step_s

    return result
