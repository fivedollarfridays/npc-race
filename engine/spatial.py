"""Spatial neighbor lookup for race simulation (T34.5).

Replaces O(n^2) loops in drafting/lateral with sorted-position
O(1) neighbor lookup using bisect.
"""

import bisect
from typing import Any

CarState = dict[str, Any]


class SortedCarIndex:
    """Index of car states sorted by distance for fast neighbor lookup.

    Constructed once per tick. Uses bisect for O(log n) neighbor queries
    instead of O(n) brute-force scans per car.
    """

    def __init__(self, states: list[CarState]) -> None:
        active = [(s["distance"], s["car_idx"], s)
                  for s in states if not s["finished"]]
        self._sorted = sorted(active, key=lambda t: t[0])
        self._distances = [t[0] for t in self._sorted]
        self._by_idx: dict[int, CarState] = {s["car_idx"]: s for s in states}

    def neighbors(self, car_idx: int, max_distance: float) -> list[CarState]:
        """Return active cars within max_distance of car_idx.

        Excludes the car itself and finished cars (already filtered
        at construction time).
        """
        car = self._by_idx[car_idx]
        car_dist = car["distance"]
        lo = bisect.bisect_left(self._distances, car_dist - max_distance)
        hi = bisect.bisect_right(self._distances, car_dist + max_distance)
        return [self._sorted[i][2] for i in range(lo, hi)
                if self._sorted[i][1] != car_idx]
