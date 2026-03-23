"""Lap accumulator — collects per-car per-lap data during simulation.

Tracks state each tick and freezes lap entries on lap completion,
without storing full replay frames.
"""

from __future__ import annotations


class LapAccumulator:
    """Collects per-car per-lap summaries during a race simulation."""

    def __init__(self) -> None:
        self._laps: dict[str, list[dict]] = {}
        self._current: dict[str, dict] = {}

    def on_tick(
        self, states: list[dict], positions: dict[str, int], tick: int,
    ) -> None:
        """Update current-lap buffer for each car from tick data."""
        for state in states:
            name = state["name"]
            pit_status = state["pit_state"]["status"]

            if name not in self._current:
                self._current[name] = {
                    "position": positions.get(name, 0),
                    "tire_compound": state["tire_compound"],
                    "tire_wear": state["tire_wear"],
                    "fuel_kg": state["fuel_kg"],
                    "max_fuel_kg": state["max_fuel_kg"],
                    "pitted_this_lap": False,
                    "_prev_pit_status": pit_status,
                }
            else:
                buf = self._current[name]
                buf["position"] = positions.get(name, 0)
                buf["tire_compound"] = state["tire_compound"]
                buf["tire_wear"] = state["tire_wear"]
                buf["fuel_kg"] = state["fuel_kg"]
                buf["max_fuel_kg"] = state["max_fuel_kg"]

                prev = buf["_prev_pit_status"]
                if prev == "racing" and pit_status != "racing":
                    buf["pitted_this_lap"] = True
                buf["_prev_pit_status"] = pit_status

    def on_lap_complete(
        self, car_name: str, lap: int, lap_time: float,
    ) -> None:
        """Freeze the current-lap buffer as a completed lap entry."""
        buf = self._current.get(car_name, {})
        max_fuel = buf.get("max_fuel_kg", 1.0) or 1.0
        entry = {
            "lap": lap,
            "time_s": lap_time,
            "position": buf.get("position", 0),
            "tire_compound": buf.get("tire_compound", "unknown"),
            "tire_wear": buf.get("tire_wear", 0.0),
            "pit_stop": buf.get("pitted_this_lap", False),
            "fuel_remaining_pct": buf.get("fuel_kg", 0.0) / max_fuel,
        }
        self._laps.setdefault(car_name, []).append(entry)
        # Reset buffer for next lap
        self._current[car_name] = {
            "position": buf.get("position", 0),
            "tire_compound": buf.get("tire_compound", "unknown"),
            "tire_wear": buf.get("tire_wear", 0.0),
            "fuel_kg": buf.get("fuel_kg", 0.0),
            "max_fuel_kg": buf.get("max_fuel_kg", 1.0),
            "pitted_this_lap": False,
            "_prev_pit_status": buf.get("_prev_pit_status", "racing"),
        }

    def get_lap_summaries(self) -> dict[str, list[dict]]:
        """Return per-car list of lap summary dicts."""
        return dict(self._laps)

    def get_race_summary(self) -> dict:
        """Return aggregate race summary across all cars."""
        if not self._laps:
            return {}
        summary: dict[str, dict] = {}
        for car_name, laps in self._laps.items():
            times = [e["time_s"] for e in laps]
            summary[car_name] = {
                "total_laps": len(laps),
                "total_time_s": sum(times),
                "best_lap_s": min(times),
                "avg_lap_s": sum(times) / len(times),
                "pit_stops": sum(1 for e in laps if e["pit_stop"]),
                "final_position": laps[-1]["position"],
            }
        return summary
