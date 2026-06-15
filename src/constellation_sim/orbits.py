"""Circular-orbit propagation and coordinate-frame conversions.

The simulator uses a circular two-body model. For a constellation study this is
the right altitude of fidelity: it captures the geometry that drives link
visibility, path length and latency, while staying simple enough to read and
test. (Perturbations such as J2 are noted as future work in the README.)

Two frames are used:

- **ECI** (Earth-Centred Inertial): does not rotate with the Earth; orbits are
  naturally described here.
- **ECEF** (Earth-Centred Earth-Fixed): rotates with the Earth, so ground
  stations are stationary here. All link geometry is computed in ECEF.

The conversion between them is a rotation about the z-axis by the Greenwich
hour angle ``theta = EARTH_ROTATION_RATE * t``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .constants import EARTH_RADIUS_KM, EARTH_ROTATION_RATE, MU_EARTH


@dataclass(frozen=True)
class Orbit:
    """A single circular orbit defined by classical-ish orbital elements.

    Parameters
    ----------
    altitude_km:
        Height above the mean Earth radius (km).
    inclination_deg:
        Orbital-plane tilt relative to the equator (deg).
    raan_deg:
        Right ascension of the ascending node (deg) — the swivel of the plane
        about the Earth's axis.
    arg_at_epoch_deg:
        Angular position of the satellite within its plane at t=0 (deg),
        measured from the ascending node. For a circular orbit there is no
        distinct argument of perigee, so this is the along-track phase.
    """

    altitude_km: float
    inclination_deg: float
    raan_deg: float
    arg_at_epoch_deg: float

    @property
    def semi_major_axis_km(self) -> float:
        """Orbit radius from Earth's centre (km)."""
        return EARTH_RADIUS_KM + self.altitude_km

    @property
    def mean_motion_rad_s(self) -> float:
        """Angular rate around the orbit (rad/s): n = sqrt(mu / a^3)."""
        a = self.semi_major_axis_km
        return math.sqrt(MU_EARTH / (a ** 3))

    @property
    def period_s(self) -> float:
        """Orbital period (s)."""
        return 2.0 * math.pi / self.mean_motion_rad_s

    def position_eci(self, t: float) -> np.ndarray:
        """Position vector in the ECI frame at time ``t`` seconds (km).

        The satellite advances along its circular orbit by ``n * t``. We build
        the position in the orbital plane, then apply the inclination and RAAN
        rotations to place that plane in inertial space.
        """
        a = self.semi_major_axis_km
        theta = math.radians(self.arg_at_epoch_deg) + self.mean_motion_rad_s * t

        # Position in the orbital plane (perifocal-like, circular).
        r_plane = np.array([a * math.cos(theta), a * math.sin(theta), 0.0])

        inc = math.radians(self.inclination_deg)
        raan = math.radians(self.raan_deg)

        # Rotate by inclination about the x-axis, then by RAAN about the z-axis.
        r = _rot_z(raan) @ _rot_x(inc) @ r_plane
        return r

    def position_ecef(self, t: float) -> np.ndarray:
        """Position vector in the rotating ECEF frame at time ``t`` (km)."""
        return eci_to_ecef(self.position_eci(t), t)


def _rot_x(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _rot_z(angle_rad: float) -> np.ndarray:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def eci_to_ecef(r_eci: np.ndarray, t: float) -> np.ndarray:
    """Rotate an ECI vector into ECEF at time ``t`` (Earth has spun by theta)."""
    theta = EARTH_ROTATION_RATE * t
    return _rot_z(-theta) @ r_eci


def geodetic_to_ecef(lat_deg: float, lon_deg: float, alt_km: float = 0.0) -> np.ndarray:
    """Convert latitude/longitude/altitude to an ECEF vector (km).

    Uses a spherical Earth, consistent with the rest of the model.
    """
    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    r = EARTH_RADIUS_KM + alt_km
    return np.array([
        r * math.cos(lat) * math.cos(lon),
        r * math.cos(lat) * math.sin(lon),
        r * math.sin(lat),
    ])


def ecef_to_geodetic(r_ecef: np.ndarray) -> tuple[float, float, float]:
    """Convert an ECEF vector (km) back to (lat_deg, lon_deg, alt_km)."""
    x, y, z = r_ecef
    radius = float(np.linalg.norm(r_ecef))
    lat = math.degrees(math.asin(z / radius))
    lon = math.degrees(math.atan2(y, x))
    return lat, lon, radius - EARTH_RADIUS_KM
