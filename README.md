# Satellite Latency Router

A small Python program that shows how **Starlink-style satellites route internet
traffic** between two cities, and finds the path with the **lowest latency**.

A city usually can't reach a far-away city through a single satellite, so the
signal hops from one satellite to the next until it can come back down near the
destination. Each hop adds a little delay because signals travel at the speed of
light. This program builds a small network of satellites and cities, then uses
**Dijkstra's algorithm** to find the fastest route.

## Example output

```
Routing internet traffic: Seattle -> London

Lowest-latency path:
   Seattle
   SAT(58,-125)
   SAT(58,-97)
   SAT(58,-69)
   SAT(58,-41)
   SAT(58,-13)
   London

Satellite hops : 6
One-way latency: 32.3 ms
Round-trip (RTT): 64.7 ms

(For comparison, fiber Seattle<->London is ~130-140 ms RTT.)
```

The ~65 ms round trip is much faster than fiber over the same distance — which
is exactly why low-orbit satellites are useful for long-haul links.

## Run it

```bash
python satellite_router.py
```

Only uses the Python standard library — nothing to install.

## Run the tests

```bash
pip install pytest
pytest
```

## How it works

The program is one file, `satellite_router.py`, with four small steps:

1. **Place the nodes** — Cities and satellites are given a latitude, longitude,
   and altitude, then converted to 3D coordinates so we can measure real
   straight-line distances (`to_xyz`).
2. **Build the network** — Two nodes get a link if they're close enough: a city
   reaches a satellite overhead, and a satellite reaches nearby satellites.
   Each link's "cost" is its latency, `distance / speed_of_light` (`build_graph`).
3. **Find the fastest path** — Dijkstra's algorithm walks the network and finds
   the route with the lowest total latency (`shortest_path`).
4. **Print the result** — The path, number of hops, and the latency.

## Things I could add next

- More cities and satellites, or a moving constellation over time.
- A simple plot of the route on a map.
- Routing that also avoids overloaded links, not just the shortest one.

---

Built as a learning project exploring the kind of networking and routing
problems behind a satellite internet system like Starlink.
