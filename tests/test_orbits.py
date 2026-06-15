"""Tests for orbital mechanics and frame conversions."""

import math

import numpy as np
import pytest

from constellation_sim.constants import EARTH_RADIUS_KM, MU_EARTH
from constellation_sim.orbits import (
    Orbit,
    ecef_to_geodetic,
    geodetic_to_ecef,
)


def test_circular_orbit_radius_is_constant():
    orbit = Orbit(altitude_km=550.0, inclination_deg=53.0, raan_deg=40.0, arg_at_epoch_deg=10.0)
    expected_r = EARTH_RADIUS_KM + 550.0
    for t in np.linspace(0, orbit.period_s, 25):
        r = np.linalg.norm(orbit.position_eci(float(t)))
        assert r == pytest.approx(expected_r, rel=1e-9)


def test_period_matches_keplers_third_law():
    orbit = Orbit(altitude_km=550.0, inclination_deg=53.0, raan_deg=0.0, arg_at_epoch_deg=0.0)
    a = EARTH_RADIUS_KM + 550.0
    expected = 2 * math.pi * math.sqrt(a ** 3 / MU_EARTH)
    assert orbit.period_s == pytest.approx(expected, rel=1e-12)
    # ~550 km LEO period is about 95-96 minutes.
    assert 90 * 60 < orbit.period_s < 100 * 60


def test_returns_to_start_after_one_period():
    orbit = Orbit(altitude_km=550.0, inclination_deg=53.0, raan_deg=20.0, arg_at_epoch_deg=0.0)
    start = orbit.position_eci(0.0)
    after = orbit.position_eci(orbit.period_s)
    assert np.allclose(start, after, atol=1e-6)


def test_inclination_bounds_z_amplitude():
    # Max latitude reached should equal the inclination for a circular orbit.
    inc = 53.0
    orbit = Orbit(altitude_km=550.0, inclination_deg=inc, raan_deg=0.0, arg_at_epoch_deg=0.0)
    max_lat = 0.0
    for t in np.linspace(0, orbit.period_s, 400):
        _, _, _ = ecef_to_geodetic(orbit.position_eci(float(t)))
        lat = math.degrees(math.asin(orbit.position_eci(float(t))[2] /
                                     (EARTH_RADIUS_KM + 550.0)))
        max_lat = max(max_lat, abs(lat))
    assert max_lat == pytest.approx(inc, abs=0.5)


def test_geodetic_roundtrip():
    for lat, lon in [(47.61, -122.33), (51.51, -0.13), (-33.87, 151.21), (0.0, 0.0)]:
        ecef = geodetic_to_ecef(lat, lon, 0.0)
        rlat, rlon, ralt = ecef_to_geodetic(ecef)
        assert rlat == pytest.approx(lat, abs=1e-6)
        assert rlon == pytest.approx(lon, abs=1e-6)
        assert ralt == pytest.approx(0.0, abs=1e-6)
