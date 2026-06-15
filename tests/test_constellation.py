"""Tests for Walker-Delta constellation construction."""

import pytest

from constellation_sim.constellation import walker_delta


def test_count_and_ids_unique():
    sats = walker_delta(num_planes=8, sats_per_plane=10, inclination_deg=53.0, altitude_km=550.0)
    assert len(sats) == 80
    assert len({s.sat_id for s in sats}) == 80


def test_planes_and_slots_assigned():
    sats = walker_delta(num_planes=3, sats_per_plane=4, inclination_deg=53.0, altitude_km=550.0)
    assert {s.plane for s in sats} == {0, 1, 2}
    assert {s.slot for s in sats} == {0, 1, 2, 3}


def test_common_altitude_and_inclination():
    sats = walker_delta(num_planes=3, sats_per_plane=3, inclination_deg=53.0, altitude_km=550.0)
    for s in sats:
        assert s.orbit.altitude_km == 550.0
        assert s.orbit.inclination_deg == 53.0


def test_invalid_phasing_factor_rejected():
    with pytest.raises(ValueError):
        walker_delta(num_planes=3, sats_per_plane=3, inclination_deg=53.0,
                     altitude_km=550.0, phasing_factor=3)
