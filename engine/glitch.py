"""Glitch engine -- code quality affects car reliability.

Better code -> higher reliability -> fewer glitches -> faster car.
Glitches replace part output with default for a duration.
"""

import random

# Default glitch durations per part (ticks at 30 Hz)
GLITCH_DURATIONS: dict[str, int] = {
    "engine_map": 30,      # 1.0s -- torque drops
    "gearbox": 10,         # 0.3s -- delayed shift
    "ers_deploy": 15,      # 0.5s -- deploy cuts
    "ers_harvest": 15,     # 0.5s -- harvest cuts
    "brake_bias": 20,      # 0.7s -- bias drift
    "suspension": 15,      # 0.5s -- ride height oscillation
    "cooling": 20,         # 0.7s -- cooling reduced
    "fuel_mix": 15,        # 0.5s -- lambda locked
    "differential": 15,    # 0.5s -- lock fixed
    "strategy": 1,         # 0.03s -- ignored this tick
}


class GlitchEngine:
    """Manages reliability-based glitches for all cars."""

    def __init__(self, reliability_scale: float = 0.3):
        self.reliability_scale = reliability_scale
        # Active glitches: {car_idx: {part_name: remaining_ticks}}
        self._active: dict[int, dict[str, int]] = {}

    def should_glitch(self, part_name: str, reliability: float,
                      tick: int, rng: random.Random) -> bool:
        """Roll against reliability. Returns True if part should glitch."""
        if self.reliability_scale <= 0:
            return False
        # Glitch probability = (1 - reliability) * scale
        prob = (1.0 - reliability) * self.reliability_scale
        return rng.random() < prob

    def get_glitch_duration(self, part_name: str) -> int:
        """Get glitch duration in ticks for a part."""
        return GLITCH_DURATIONS.get(part_name, 15)

    def set_active_glitch(self, part_name: str, car_idx: int,
                          duration: int) -> None:
        """Set a glitch as active for a car's part."""
        if car_idx not in self._active:
            self._active[car_idx] = {}
        self._active[car_idx][part_name] = duration

    def is_glitching(self, part_name: str, car_idx: int) -> bool:
        """Check if a part is currently glitching."""
        return self._active.get(car_idx, {}).get(part_name, 0) > 0

    def tick_glitches(self, car_idx: int) -> None:
        """Decrement all active glitch durations for a car."""
        if car_idx not in self._active:
            return
        expired = []
        for part, remaining in self._active[car_idx].items():
            self._active[car_idx][part] = remaining - 1
            if remaining - 1 <= 0:
                expired.append(part)
        for part in expired:
            del self._active[car_idx][part]
