"""Integration test for the simulation driver and metrics."""

import pytest

from constellation_sim import GroundNode, run_simulation, summarize, walker_delta


def _sim():
    sats = walker_delta(num_planes=18, sats_per_plane=18, inclination_deg=53.0, altitude_km=550.0)
    ground = [GroundNode("Seattle", 47.61, -122.33), GroundNode("London", 51.51, -0.13)]
    return run_simulation(sats, ground, "Seattle", "London", duration_s=300.0, step_s=30.0)


def test_simulation_produces_aligned_timeseries():
    result = _sim()
    assert len(result.times_s) == len(result.routes) == 11  # 0..300 step 30
    assert result.source == "Seattle" and result.target == "London"


def test_dense_constellation_connects_and_latency_is_physical():
    result = _sim()
    summary = summarize(result)
    # A dense LEO shell should reach a transatlantic pair most of the time.
    assert summary.availability_pct > 0.0
    # Seattle<->London RTT over LEO is on the order of tens of ms, not seconds.
    assert summary.min_latency_ms < 200.0
    assert summary.mean_hops >= 1


def test_unknown_endpoint_raises():
    sats = walker_delta(num_planes=4, sats_per_plane=4, inclination_deg=53.0, altitude_km=550.0)
    ground = [GroundNode("A", 0.0, 0.0)]
    with pytest.raises(ValueError):
        run_simulation(sats, ground, "A", "Nope", duration_s=30.0, step_s=30.0)
