"""Plotting helpers for the demo.

These functions are deliberately dependency-light: they use only matplotlib and
numpy and render onto an equirectangular (lat/lon) world for the 2D views, so
there is no heavy GIS stack to install. Each returns the matplotlib ``Figure``
so callers can show, save, or further customise it.
"""

from __future__ import annotations

import numpy as np

from .constellation import Satellite
from .network import GroundNode, build_network_graph
from .orbits import ecef_to_geodetic
from .simulate import SimulationResult


def _lazy_plt():
    import matplotlib

    matplotlib.use("Agg")  # headless-safe; callers can override before plotting
    import matplotlib.pyplot as plt

    return plt


def plot_latency_timeseries(result: SimulationResult, path: str | None = None):
    """Plot end-to-end RTT latency over the run."""
    plt = _lazy_plt()
    minutes = [t / 60.0 for t in result.times_s]
    latencies = result.latencies_ms

    fig, ax = plt.subplots(figsize=(10, 4))
    # Break the line at outages so gaps are visible.
    finite = [l if np.isfinite(l) else np.nan for l in latencies]
    ax.plot(minutes, finite, color="#1f77b4", lw=1.8)
    ax.set_title(f"End-to-end latency: {result.source} -> {result.target}")
    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Round-trip latency (ms)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120)
    return fig


def plot_route_snapshot(
    satellites: list[Satellite],
    ground_nodes: list[GroundNode],
    result: SimulationResult,
    step_index: int,
    path: str | None = None,
):
    """Plot the chosen route on a world map at a single timestep."""
    plt = _lazy_plt()
    t = result.times_s[step_index]
    route = result.routes[step_index]

    # Map every node id to its lat/lon at this instant.
    coords: dict[str, tuple[float, float]] = {}
    for sat in satellites:
        lat, lon, _ = ecef_to_geodetic(sat.position_ecef(t))
        coords[sat.sat_id] = (lat, lon)
    for g in ground_nodes:
        coords[g.name] = (g.lat_deg, g.lon_deg)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    _draw_world(ax)

    # All satellites as faint dots.
    sat_lats = [coords[s.sat_id][0] for s in satellites]
    sat_lons = [coords[s.sat_id][1] for s in satellites]
    ax.scatter(sat_lons, sat_lats, s=6, color="#888", alpha=0.5, label="satellites")

    # Ground nodes.
    for g in ground_nodes:
        ax.scatter([g.lon_deg], [g.lat_deg], s=40, marker="^", color="#d62728", zorder=5)
        ax.annotate(g.name, (g.lon_deg, g.lat_deg), textcoords="offset points",
                    xytext=(4, 4), fontsize=8)

    # The route itself.
    if route.is_connected:
        lats = [coords[n][0] for n in route.path]
        lons = [coords[n][1] for n in route.path]
        ax.plot(lons, lats, color="#2ca02c", lw=2.2, marker="o", ms=4, zorder=6,
                label=f"route ({route.hop_count} hops)")
        rtt = 2.0 * route.total_delay_s * 1000.0
        title = f"t = {t/60:.1f} min   RTT ~ {rtt:.1f} ms   {route.hop_count} hops"
    else:
        title = f"t = {t/60:.1f} min   (no route)"

    ax.set_title(title)
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120)
    return fig


def plot_ground_tracks(
    satellites: list[Satellite],
    duration_s: float,
    step_s: float,
    sample_planes: int | None = None,
    path: str | None = None,
):
    """Plot the sub-satellite ground tracks for (a sample of) the constellation."""
    plt = _lazy_plt()
    fig, ax = plt.subplots(figsize=(11, 5.5))
    _draw_world(ax)

    planes = sorted({s.plane for s in satellites})
    if sample_planes is not None:
        planes = planes[:sample_planes]

    times = np.arange(0.0, duration_s + 1e-9, step_s)
    for sat in satellites:
        if sat.plane not in planes or sat.slot != 0:
            continue  # one representative satellite per plane keeps it readable
        lats, lons = [], []
        for t in times:
            lat, lon, _ = ecef_to_geodetic(sat.position_ecef(float(t)))
            lats.append(lat)
            lons.append(lon)
        ax.scatter(lons, lats, s=3, alpha=0.6)

    ax.set_title("Sub-satellite ground tracks")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=120)
    return fig


def _draw_world(ax) -> None:
    """Draw a simple equirectangular world frame (no external map data)."""
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitude (deg)")
    ax.set_ylabel("Latitude (deg)")
    ax.set_xticks(range(-180, 181, 60))
    ax.set_yticks(range(-90, 91, 30))
    ax.grid(True, alpha=0.25)
    ax.axhline(0, color="#aaa", lw=0.8)  # equator
    ax.set_facecolor("#f4f8ff")
