"""Track speed profile — optimal speed at every point for a given car.

Three-pass algorithm:
1. Max cornering speed from curvature + grip
2. Backward braking pass — can't exceed what's reachable by braking
3. Forward acceleration pass — can't exceed what's reachable by accelerating
"""

from .physics import (compute_target_speed, MAX_SPEED, BRAKE_BASE, ACCEL_BASE,
                      ACCEL_POWER_FACTOR)
import bisect


def compute_speed_profile(track_points, curvatures, distances, track_length,
                          car_stats: dict) -> list[float]:
    """Compute optimal speed at every track point for a given car."""
    n = len(curvatures)
    if n == 0:
        return []

    power = car_stats.get("power", 0.5)
    grip = car_stats.get("grip", 0.5)
    weight = car_stats.get("weight", 0.5)

    # Pass 1: max cornering speed at each point
    profile = []
    for i in range(n):
        target = compute_target_speed(
            power=power, grip=grip, weight=weight,
            curvature=curvatures[i], throttle=1.0,
            tire_grip_mult=1.0, power_mode=1.0,
            boost_active=False, setup=None)
        profile.append(min(target, MAX_SPEED))

    # Pass 2: backward braking — ensure we can brake in time
    # Braking deceleration ~ BRAKE_BASE km/h per second
    brake_decel = BRAKE_BASE * 3.6  # convert to km/h per second approx
    for i in range(n - 2, -1, -1):
        seg_dist = distances[i + 1] - distances[i] if i + 1 < len(distances) else 1.0
        if seg_dist <= 0:
            seg_dist = 0.1
        # Max speed at i such that we can brake to profile[i+1]
        # v_max^2 = v_next^2 + 2 * decel * dist (kinematic equation)
        v_next = profile[(i + 1) % n]
        decel_ms2 = brake_decel / 3.6  # m/s^2
        # Convert seg_dist from sim units to approximate meters
        seg_m = seg_dist * (track_length / max(distances[-1], 1)) if distances[-1] > 0 else seg_dist
        v_next_ms = v_next / 3.6
        v_max_ms2 = v_next_ms ** 2 + 2 * decel_ms2 * seg_m
        v_max_kmh = (v_max_ms2 ** 0.5) * 3.6 if v_max_ms2 > 0 else 0
        profile[i] = min(profile[i], v_max_kmh, MAX_SPEED)

    # Pass 3: forward acceleration — can't accelerate faster than physics allows
    accel_rate = (ACCEL_BASE + power * ACCEL_POWER_FACTOR) * 2.0  # km/h per second
    for i in range(1, n):
        seg_dist = distances[i] - distances[i - 1] if i < len(distances) else 1.0
        if seg_dist <= 0:
            seg_dist = 0.1
        seg_m = seg_dist * (track_length / max(distances[-1], 1)) if distances[-1] > 0 else seg_dist
        v_prev_ms = profile[i - 1] / 3.6
        accel_ms2 = accel_rate / 3.6
        v_max_ms2 = v_prev_ms ** 2 + 2 * accel_ms2 * seg_m
        v_max_kmh = (v_max_ms2 ** 0.5) * 3.6 if v_max_ms2 > 0 else 0
        profile[i] = min(profile[i], v_max_kmh, MAX_SPEED)

    return profile


def get_profile_speed(profile: list[float], distance: float,
                      distances: list[float], track_length: float) -> float:
    """Look up optimal speed at a given distance (interpolated)."""
    if not profile or not distances:
        return 200.0
    d = distance % track_length if track_length > 0 else distance
    if d < 0:
        d += track_length
    idx = bisect.bisect_right(distances, d) - 1
    idx = max(0, min(idx, len(profile) - 1))
    return profile[idx]
