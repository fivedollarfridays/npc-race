"""
Track generation for NPC Race.

Generates closed-loop tracks from random control points using
Catmull-Rom spline interpolation.
"""

import math
import random


def generate_track(seed=42, num_points=12, scale=300, center=(400, 350)):
    """Generate a closed-loop track from control points."""
    rng = random.Random(seed)
    cx, cy = center
    points = []
    for i in range(num_points):
        angle = (2 * math.pi * i) / num_points
        r = scale + rng.uniform(-80, 80)
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    return points


def interpolate_track(control_points, resolution=500):
    """Catmull-Rom spline interpolation for smooth track."""
    n = len(control_points)
    track = []

    for i in range(n):
        p0 = control_points[(i - 1) % n]
        p1 = control_points[i]
        p2 = control_points[(i + 1) % n]
        p3 = control_points[(i + 2) % n]

        seg_points = resolution // n
        for j in range(seg_points):
            t = j / seg_points
            t2 = t * t
            t3 = t2 * t

            x = 0.5 * ((2 * p1[0]) +
                        (-p0[0] + p2[0]) * t +
                        (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
                        (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) +
                        (-p0[1] + p2[1]) * t +
                        (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
                        (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            track.append((x, y))

    return track


def compute_track_data(track_points):
    """Compute distances and curvatures for each track point."""
    n = len(track_points)
    distances = [0.0]
    curvatures = []

    for i in range(1, n):
        dx = track_points[i][0] - track_points[i - 1][0]
        dy = track_points[i][1] - track_points[i - 1][1]
        distances.append(distances[-1] + math.sqrt(dx * dx + dy * dy))

    for i in range(n):
        p0 = track_points[(i - 1) % n]
        p1 = track_points[i]
        p2 = track_points[(i + 1) % n]

        dx1 = p1[0] - p0[0]
        dy1 = p1[1] - p0[1]
        dx2 = p2[0] - p1[0]
        dy2 = p2[1] - p1[1]

        cross = abs(dx1 * dy2 - dy1 * dx2)
        d1 = math.sqrt(dx1 * dx1 + dy1 * dy1) + 0.001
        d2 = math.sqrt(dx2 * dx2 + dy2 * dy2) + 0.001
        curvatures.append(cross / (d1 * d2))

    total_length = distances[-1]
    # Add closing segment
    dx = track_points[0][0] - track_points[-1][0]
    dy = track_points[0][1] - track_points[-1][1]
    total_length += math.sqrt(dx * dx + dy * dy)

    return distances, curvatures, total_length


def compute_track_headings(track_points):
    """Compute heading angle (radians) at each track point.

    Returns a list of atan2-based heading angles, one per point,
    using the direction vector to the next point (wrapping at end).
    """
    n = len(track_points)
    headings = []
    for i in range(n):
        nxt = (i + 1) % n
        dx = track_points[nxt][0] - track_points[i][0]
        dy = track_points[nxt][1] - track_points[i][1]
        headings.append(math.atan2(dy, dx))
    return headings


def get_curvature_at(distance, distances, curvatures, track_length):
    """Get track curvature at a given distance along the track."""
    d = distance % track_length
    if d < 0:
        d += track_length
    for i in range(len(distances) - 1):
        if distances[i] <= d <= distances[i + 1]:
            return curvatures[i]
    return 0.0
