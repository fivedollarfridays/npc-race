"""Track speed profile — optimal speed at every point for a given car.

Three-pass algorithm:
1. Max cornering speed from curvature + grip
2. Backward braking pass — can't exceed what's reachable by braking
3. Forward acceleration pass — can't exceed what's reachable by accelerating
"""

from .physics import (MAX_SPEED)
import bisect


def compute_speed_profile(track_points, curvatures, distances, track_length,
                          car_stats: dict, real_length_m: float = 5793) -> list[float]:
    """Compute optimal speed at every track point for a given car."""
    n = len(curvatures)
    if n == 0:
        return []

    grip = car_stats.get("grip", 0.5)

    # Pass 1: max cornering speed from physics: v = sqrt(mu * g * R)
    # Effective mu includes downforce: real F1 ~3.5-4.5 at speed
    mu = 3.2 + grip * 1.6  # 3.2 base, up to 4.8 with high grip
    # Scale: sim units to real meters
    real_per_sim = real_length_m / max(1, track_length)
    profile = []
    for i in range(n):
        curv = curvatures[i]
        if curv < 0.001:
            profile.append(MAX_SPEED)
            continue
        # Convert sim curvature to real radius
        radius_real = (1.0 / curv) * real_per_sim
        v_ms = (mu * 9.81 * radius_real) ** 0.5
        v_kmh = v_ms * 3.6
        profile.append(min(v_kmh, MAX_SPEED))

    # Pass 2: backward braking — v_max^2 = v_next^2 + 2*a*d
    # Real F1 braking: 5G = 49 m/s^2
    decel_ms2 = 5.0 * 9.81  # 5G braking
    for i in range(n - 2, -1, -1):
        seg_dist = distances[i + 1] - distances[i] if i + 1 < len(distances) else 1.0
        if seg_dist <= 0:
            seg_dist = 0.1
        seg_m = seg_dist * real_per_sim  # convert sim units to meters
        v_next_ms = profile[(i + 1) % n] / 3.6
        v_max_ms2 = v_next_ms ** 2 + 2 * decel_ms2 * seg_m
        v_max_kmh = (v_max_ms2 ** 0.5) * 3.6 if v_max_ms2 > 0 else 0
        profile[i] = min(profile[i], v_max_kmh, MAX_SPEED)

    # Pass 3: forward acceleration — F1 ~1.5G average acceleration
    accel_ms2 = 1.5 * 9.81  # ~15 m/s^2 typical F1 acceleration
    for i in range(1, n):
        seg_dist = distances[i] - distances[i - 1] if i < len(distances) else 1.0
        if seg_dist <= 0:
            seg_dist = 0.1
        seg_m = seg_dist * real_per_sim
        v_prev_ms = profile[i - 1] / 3.6
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
