"""
constellation_sim
=================

A physics-based simulator for a Starlink-style low-Earth-orbit (LEO)
satellite constellation and the dynamic network that routes traffic across it.

The package is split into small, independently testable modules:

- ``constants``      : physical constants (Earth, orbital mechanics, light speed).
- ``orbits``         : Keplerian circular-orbit propagation and frame conversions.
- ``constellation``  : Walker-Delta constellation construction.
- ``network``        : link visibility, inter-satellite-link topology, graph build.
- ``routing``        : least-latency path finding (Dijkstra) over the live graph.
- ``simulate``       : time-stepped driver that produces a route/metric timeseries.
- ``metrics``        : summary statistics (latency, hops, handovers, availability).
- ``visualize``      : 2D/3D plots and animation helpers for the demo.

See the project README for the motivation and the end-to-end demo.
"""

from .constants import (
    EARTH_RADIUS_KM,
    MU_EARTH,
    SPEED_OF_LIGHT_KMS,
    EARTH_ROTATION_RATE,
)
from .orbits import Orbit
from .constellation import Satellite, walker_delta
from .network import GroundNode, build_network_graph, is_visible, has_line_of_sight
from .routing import shortest_path
from .simulate import SimulationResult, run_simulation
from .metrics import summarize

__all__ = [
    "EARTH_RADIUS_KM",
    "MU_EARTH",
    "SPEED_OF_LIGHT_KMS",
    "EARTH_ROTATION_RATE",
    "Orbit",
    "Satellite",
    "walker_delta",
    "GroundNode",
    "build_network_graph",
    "is_visible",
    "has_line_of_sight",
    "shortest_path",
    "SimulationResult",
    "run_simulation",
    "summarize",
]

__version__ = "0.1.0"
