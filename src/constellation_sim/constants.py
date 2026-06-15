"""Physical constants used across the simulator.

All distances are in kilometres and all times in seconds unless noted otherwise.
Values are standard published constants; keeping them in one place makes the
physics easy to audit and the rest of the code unit-consistent.
"""

# Earth
EARTH_RADIUS_KM: float = 6371.0
"""Mean Earth radius (km). Used for the spherical-Earth occlusion model."""

EARTH_ROTATION_RATE: float = 7.2921159e-5
"""Earth sidereal rotation rate (rad/s)."""

# Gravity
MU_EARTH: float = 398600.4418
"""Earth standard gravitational parameter, G*M (km^3 / s^2)."""

# Signal propagation
SPEED_OF_LIGHT_KMS: float = 299792.458
"""Speed of light (km/s). Free-space links (ISLs, RF up/downlinks) propagate
at ~c; this dominates end-to-end latency over long satellite paths."""

# Modelling defaults
DEFAULT_MIN_ELEVATION_DEG: float = 25.0
"""Minimum elevation angle (deg) for a ground node to use a satellite. Below
this, atmospheric path length and obstructions make the link impractical."""

DEFAULT_GROUND_ALTITUDE_KM: float = 0.0
"""Assumed altitude of ground terminals (km)."""
