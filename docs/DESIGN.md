# Design Notes

This document records the engineering decisions behind `constellation-sim` —
the kind of write-up a design review would expect, and a useful interview
talking point.

## Goal

Simulate a Starlink-style LEO constellation and answer one question well:
**what is the lowest-latency path between two points on Earth, and how does it
change as the satellites move?**

## Frames and coordinates

Two reference frames are used deliberately:

- **ECI** (Earth-Centred Inertial) — does not rotate; orbital motion is simplest
  here. We build each satellite's position in its orbital plane, then apply
  inclination (rotation about x) and RAAN (rotation about z).
- **ECEF** (Earth-Centred Earth-Fixed) — rotates with the Earth. Ground
  terminals are stationary here, so *all link geometry is computed in ECEF.*

The bridge is a single z-rotation by the Greenwich hour angle
`theta = EARTH_ROTATION_RATE * t`. Doing visibility and ISL math in one
consistent frame removes a whole class of bugs.

## Orbital model — why circular two-body

A circular two-body model is the right altitude of fidelity for a
*constellation geometry and routing* study:

- It captures what actually drives the answer: satellite positions over time,
  link ranges, elevation angles, and therefore latency and handovers.
- It is analytic and fast — important because the driver rebuilds the graph at
  every timestep.
- It is easy to verify: orbit radius is constant, period obeys Kepler's third
  law, and the orbit closes after one period (all asserted in tests).

Perturbations (J2, drag) and real ephemerides (SGP4/TLE) are listed as roadmap
items; they refine positions but do not change the architecture.

## Network model

At each timestep the world is a weighted undirected graph:

- **Nodes:** satellites + ground terminals.
- **Ground↔satellite edges:** allowed when the satellite is above a minimum
  **elevation angle** (default 25°), which approximates the practical link
  cone of a user terminal.
- **Satellite↔satellite edges (ISLs):** a `+grid` topology — each satellite
  links to its in-plane ahead/behind neighbours and to same-slot neighbours in
  adjacent planes. Each candidate is then gated by **max range** and a
  **line-of-sight** test that rejects links whose chord passes through the
  Earth.
- **Edge weight:** one-way propagation delay `distance / c`. Latency is the
  dominant, physically unavoidable cost over these distances, so optimising it
  is the meaningful objective.

### Line-of-sight test

For two points `p1, p2`, parameterise the segment and find the closest approach
of the *line* to Earth's centre. If that closest point lies between the
endpoints and its radius is below the Earth's surface, the link is blocked.
Endpoints that face each other (closest approach outside the segment) always
have line of sight. This is O(1) and branch-clear — see
`network.has_line_of_sight`.

## Routing

Dijkstra with a binary heap (`heapq`). Non-negative propagation delays make
Dijkstra the correct and efficient choice (no need for Bellman-Ford). The path
cost equals the end-to-end one-way latency; RTT is reported as `2 ×` that.

Complexity per timestep: `O(E log V)` for routing, plus `O(N²_visibility)` for
the ground-link scan and `O(N_isl)` for the ISL edges, where the visibility
scan dominates for large shells — a natural target for the planned C++ port.

## Metrics

The run is reduced to the numbers an operator cares about:

- **Availability** — fraction of samples with any route.
- **Latency** — min/mean/max RTT over connected samples.
- **Hops** — satellites traversed (proxy for processing/serialization cost).
- **Handovers** — count of timesteps where the path changed; each change is a
  potential momentary disruption and a thing the real system must hide.

## Testing strategy

- **Physics unit tests** assert invariants (constant radius, Kepler period,
  orbit closure, inclination → max latitude, geodetic round-trip).
- **Algorithm unit tests** check Dijkstra against hand-computed graphs,
  including the "prefer lower total delay over fewer hops" case.
- **Geometry unit tests** check occlusion, elevation, and graph symmetry.
- **Integration test** runs a dense shell and asserts the transatlantic latency
  is physically plausible (tens of ms, not seconds) and availability > 0.
- **CI** runs the suite on Python 3.10–3.12 and smoke-tests the demo.

## What I would do next

1. Swap the analytic orbit for SGP4 + TLEs to route over the *real* constellation.
2. Make routing congestion-aware: edge weight `= propagation + queueing(load)`.
3. Port the per-step graph build + Dijkstra to C++ (`pybind11`) and benchmark
   against the Python reference kept in this repo.
