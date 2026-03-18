"""Dirty air model -- aerodynamic turbulence from leading car.

Following closely through corners reduces grip (turbulent wake disrupts
downforce). On straights, dirty air has minimal grip effect but may
slightly reduce top speed.
"""

DIRTY_AIR_GAP_THRESHOLD = 1.5    # seconds -- beyond this, clean air
DIRTY_AIR_GRIP_PENALTY = 0.08    # max grip loss at 0s gap (8%)
DIRTY_AIR_WEAR_MULT = 1.10       # 10% faster tire wear in dirty air
DIRTY_AIR_CURVATURE_MIN = 0.02   # only applies in corners


def compute_dirty_air_factor(
    gap_ahead_s: float, curvature: float
) -> tuple[float, float]:
    """Return (grip_multiplier, wear_multiplier) for dirty air effect.

    grip_multiplier: 0.92-1.0 (1.0 = clean air)
    wear_multiplier: 1.0-1.10 (1.10 = max dirty air wear)

    Only active when gap < threshold AND in a corner (curvature > min).
    Linear interpolation based on gap distance.
    """
    if gap_ahead_s >= DIRTY_AIR_GAP_THRESHOLD:
        return 1.0, 1.0
    if curvature < DIRTY_AIR_CURVATURE_MIN:
        return 1.0, 1.0

    # Closer gap = stronger effect. At gap=0: full penalty. At threshold: zero.
    intensity = 1.0 - (gap_ahead_s / DIRTY_AIR_GAP_THRESHOLD)
    intensity = max(0.0, min(1.0, intensity))

    grip_mult = 1.0 - DIRTY_AIR_GRIP_PENALTY * intensity
    wear_mult = 1.0 + (DIRTY_AIR_WEAR_MULT - 1.0) * intensity

    return grip_mult, wear_mult
