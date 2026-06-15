"""Walker-Delta constellation construction.

Starlink's shells are well approximated by a Walker-Delta pattern: ``P`` equally
spaced orbital planes, each holding ``S`` equally spaced satellites, with a
phase offset between adjacent planes set by the phasing factor ``F``.

This module turns a few human-readable parameters into a flat list of
``Satellite`` objects, each carrying its own :class:`~constellation_sim.orbits.Orbit`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .orbits import Orbit


@dataclass(frozen=True)
class Satellite:
    """One satellite: a stable id, its plane/slot indices, and its orbit."""

    sat_id: str
    plane: int
    slot: int
    orbit: Orbit

    def position_ecef(self, t: float) -> np.ndarray:
        return self.orbit.position_ecef(t)


def walker_delta(
    num_planes: int,
    sats_per_plane: int,
    inclination_deg: float,
    altitude_km: float,
    phasing_factor: int = 1,
) -> list[Satellite]:
    """Build a Walker-Delta constellation.

    Parameters
    ----------
    num_planes:
        Number of orbital planes ``P``.
    sats_per_plane:
        Satellites per plane ``S``.
    inclination_deg:
        Common inclination for every plane.
    altitude_km:
        Common altitude for every satellite.
    phasing_factor:
        Walker phasing ``F`` (0 <= F < P). Sets the along-track offset between
        adjacent planes: ``360 * F / (P * S)`` degrees.

    Returns
    -------
    list[Satellite]
        ``P * S`` satellites with ids of the form ``"SAT-{plane}-{slot}"``.

    Notes
    -----
    Defaults in the demo approximate Starlink's first shell
    (~550 km, 53° inclination), scaled down for a readable plot.
    """
    if not (0 <= phasing_factor < num_planes):
        raise ValueError("phasing_factor must satisfy 0 <= F < num_planes")

    total = num_planes * sats_per_plane
    satellites: list[Satellite] = []

    raan_step = 360.0 / num_planes
    slot_step = 360.0 / sats_per_plane
    phase_step = 360.0 * phasing_factor / total

    for plane in range(num_planes):
        raan = plane * raan_step
        for slot in range(sats_per_plane):
            arg = slot * slot_step + plane * phase_step
            orbit = Orbit(
                altitude_km=altitude_km,
                inclination_deg=inclination_deg,
                raan_deg=raan % 360.0,
                arg_at_epoch_deg=arg % 360.0,
            )
            satellites.append(
                Satellite(sat_id=f"SAT-{plane}-{slot}", plane=plane, slot=slot, orbit=orbit)
            )

    return satellites
