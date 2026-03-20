"""Racing line model — optimal lateral position at every track point.

Inside on corner entry, clip apex, wide on exit. Straight = center.
"""

import bisect
import math


def compute_racing_line(track_points, curvatures, headings) -> list[float]:
    """Compute optimal lateral position (-1 to +1) at every track point.

    Positive curvature change = right turn → go left (inside = negative lateral).
    Uses curvature magnitude + heading change direction.
    """
    n = len(curvatures)
    if n == 0:
        return []

    line = [0.0] * n
    for i in range(n):
        curv = curvatures[i]
        if curv < 0.005:
            line[i] = 0.0  # straight — center of track
            continue
        # Determine corner direction from heading change
        if headings and len(headings) > i:
            h_prev = headings[max(0, i - 5)]
            h_curr = headings[i]
            delta = h_curr - h_prev
            # Normalize to [-pi, pi]
            delta = (delta + math.pi) % (2 * math.pi) - math.pi
            direction = -1.0 if delta > 0 else 1.0  # go opposite to turn direction
        else:
            direction = -1.0

        # Magnitude: higher curvature = more inside
        intensity = min(1.0, curv / 0.08)  # saturate at curv=0.08
        line[i] = direction * intensity * 0.8  # max lateral = ±0.8

    # Smooth the line to avoid jitter
    smoothed = list(line)
    for _ in range(3):  # 3 smoothing passes
        for i in range(1, n - 1):
            smoothed[i] = 0.5 * smoothed[i] + 0.25 * smoothed[i - 1] + 0.25 * smoothed[i + 1]

    return smoothed


def get_line_lateral(racing_line: list[float], distance: float,
                     distances: list[float], track_length: float) -> float:
    """Look up optimal lateral position at a given distance."""
    if not racing_line or not distances:
        return 0.0
    d = distance % track_length if track_length > 0 else distance
    if d < 0:
        d += track_length
    idx = bisect.bisect_right(distances, d) - 1
    idx = max(0, min(idx, len(racing_line) - 1))
    return racing_line[idx]
