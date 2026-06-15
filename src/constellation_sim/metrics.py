"""Summary metrics over a simulation run.

These are the numbers a network engineer actually cares about: how low and how
stable is the latency, how many hops does traffic take, how often does the path
change (each change is a potential disruption / handover), and what fraction of
the time is the destination reachable at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from .simulate import SimulationResult


@dataclass(frozen=True)
class MetricsSummary:
    samples: int
    availability_pct: float
    min_latency_ms: float
    mean_latency_ms: float
    max_latency_ms: float
    min_hops: int
    mean_hops: float
    max_hops: int
    handovers: int
    """Number of timesteps where the path differed from the previous step."""

    def as_dict(self) -> dict[str, float]:
        return {
            "samples": self.samples,
            "availability_pct": round(self.availability_pct, 2),
            "min_latency_ms": round(self.min_latency_ms, 2),
            "mean_latency_ms": round(self.mean_latency_ms, 2),
            "max_latency_ms": round(self.max_latency_ms, 2),
            "min_hops": self.min_hops,
            "mean_hops": round(self.mean_hops, 2),
            "max_hops": self.max_hops,
            "handovers": self.handovers,
        }


def summarize(result: SimulationResult) -> MetricsSummary:
    """Reduce a :class:`SimulationResult` to a :class:`MetricsSummary`."""
    total = len(result.routes)
    connected = [r for r in result.routes if r.is_connected]
    n_conn = len(connected)

    if n_conn == 0:
        return MetricsSummary(
            samples=total,
            availability_pct=0.0,
            min_latency_ms=float("inf"),
            mean_latency_ms=float("inf"),
            max_latency_ms=float("inf"),
            min_hops=0,
            mean_hops=0.0,
            max_hops=0,
            handovers=0,
        )

    latencies = [2.0 * r.total_delay_s * 1000.0 for r in connected]
    hops = [r.hop_count for r in connected]

    # Count path changes across consecutive connected-state samples.
    handovers = 0
    prev_path: list[str] | None = None
    for r in result.routes:
        path = r.path if r.is_connected else None
        if prev_path is not None and path is not None and path != prev_path:
            handovers += 1
        prev_path = path if path is not None else prev_path

    return MetricsSummary(
        samples=total,
        availability_pct=100.0 * n_conn / total if total else 0.0,
        min_latency_ms=min(latencies),
        mean_latency_ms=sum(latencies) / n_conn,
        max_latency_ms=max(latencies),
        min_hops=min(hops),
        mean_hops=sum(hops) / n_conn,
        max_hops=max(hops),
        handovers=handovers,
    )
