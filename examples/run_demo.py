"""End-to-end demo: route traffic Seattle -> London over a LEO constellation.

Run from the repo root:

    python examples/run_demo.py

It builds a Starlink-like shell, simulates several minutes of motion, routes a
flow between two ground terminals, prints a metrics summary, and writes plots to
``docs/media/``.
"""

from __future__ import annotations

import os
import sys

# Allow running without installing the package.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from constellation_sim import (  # noqa: E402
    GroundNode,
    run_simulation,
    summarize,
    walker_delta,
)
from constellation_sim.visualize import (  # noqa: E402
    plot_ground_tracks,
    plot_latency_timeseries,
    plot_route_snapshot,
)

MEDIA_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "media")


def main() -> None:
    os.makedirs(MEDIA_DIR, exist_ok=True)

    # A readable Starlink-like shell: 18 planes x 18 sats at 550 km, 53 deg.
    satellites = walker_delta(
        num_planes=18,
        sats_per_plane=18,
        inclination_deg=53.0,
        altitude_km=550.0,
        phasing_factor=1,
    )

    ground = [
        GroundNode("Seattle", 47.61, -122.33),
        GroundNode("London", 51.51, -0.13),
        GroundNode("Tokyo", 35.68, 139.69),
        GroundNode("Sydney", -33.87, 151.21),
    ]

    print(f"Constellation: {len(satellites)} satellites")
    period_min = satellites[0].orbit.period_s / 60.0
    print(f"Orbital period: {period_min:.1f} min")

    result = run_simulation(
        satellites,
        ground,
        source="Seattle",
        target="London",
        duration_s=600.0,   # 10 minutes
        step_s=15.0,        # 15-second resolution
    )

    summary = summarize(result)
    print("\nMetrics (Seattle -> London):")
    for key, value in summary.as_dict().items():
        print(f"  {key:18s}: {value}")

    # Pick a representative connected step for the snapshot.
    snapshot_idx = next(
        (i for i, r in enumerate(result.routes) if r.is_connected), 0
    )

    plot_latency_timeseries(result, path=os.path.join(MEDIA_DIR, "latency.png"))
    plot_route_snapshot(
        satellites, ground, result, snapshot_idx,
        path=os.path.join(MEDIA_DIR, "route_snapshot.png"),
    )
    plot_ground_tracks(
        satellites, duration_s=period_min * 60.0, step_s=30.0,
        path=os.path.join(MEDIA_DIR, "ground_tracks.png"),
    )

    print(f"\nWrote plots to {os.path.relpath(MEDIA_DIR)}/")


if __name__ == "__main__":
    main()
