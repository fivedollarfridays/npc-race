"""Timing module — per-lap times, sector splits, fastest lap tracking."""
from __future__ import annotations

SECTOR_BOUNDARIES: tuple[float, float, float] = (0.333, 0.666, 1.0)


class CarTiming:
    """Per-car timing state."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.lap_times: list[float] = []
        self.sector_times: list[list[float]] = []
        self.current_lap_start: int = 0
        self.current_sector: int = 0
        self.current_sector_start: int = 0
        self.current_lap_sectors: list[float] = []
        self.best_lap: float | None = None
        self.best_sectors: list[float | None] = [None, None, None]
        self._prev_lap: int = 0


def get_sector_boundaries(track_dict: dict) -> tuple[float, float, float]:
    """Return sector boundary percentages from track, or default thirds."""
    return tuple(track_dict.get("sector_boundaries", SECTOR_BOUNDARIES))


def create_timing(car_names: list[str]) -> dict[str, CarTiming]:
    """Initialize timing state for all cars."""
    return {name: CarTiming(name) for name in car_names}


def _handle_lap_completion(ct: CarTiming, tick: int, tps: int) -> dict:
    """Record completed lap and reset for next lap."""
    lap_time = (tick - ct.current_lap_start) / tps
    ct.lap_times.append(lap_time)
    sector_time = (tick - ct.current_sector_start) / tps
    ct.current_lap_sectors.append(sector_time)
    ct.sector_times.append(ct.current_lap_sectors[:])
    if ct.best_lap is None or lap_time < ct.best_lap:
        ct.best_lap = lap_time
    for i, st in enumerate(ct.current_lap_sectors):
        if i < 3 and (ct.best_sectors[i] is None or st < ct.best_sectors[i]):
            ct.best_sectors[i] = st
    ct.current_lap_start = tick
    ct.current_sector = 0
    ct.current_sector_start = tick
    ct.current_lap_sectors = []
    return {"lap_completed": True, "lap_time": lap_time}


def _detect_sector(
    ct: CarTiming, distance_pct: float, tick: int, tps: int,
    boundaries: tuple[float, float, float],
) -> dict:
    """Check for sector transition within a lap."""
    new_sector = 2 if distance_pct >= boundaries[1] else (
        1 if distance_pct >= boundaries[0] else 0)
    if new_sector > ct.current_sector:
        sector_time = (tick - ct.current_sector_start) / tps
        old = ct.current_sector
        if old < 3 and (ct.best_sectors[old] is None or sector_time < ct.best_sectors[old]):
            ct.best_sectors[old] = sector_time
        ct.current_lap_sectors.append(sector_time)
        ct.current_sector = new_sector
        ct.current_sector_start = tick
        return {"sector_completed": True, "sector_time": sector_time}
    return {"sector_completed": False, "sector_time": None}


def update_timing(
    timings: dict[str, CarTiming], car_name: str, distance_pct: float,
    lap: int, tick: int, ticks_per_sec: int,
    sector_boundaries: tuple[float, float, float],
) -> dict:
    """Update timing for one car. Returns timing event dict."""
    ct = timings[car_name]
    result = {
        "lap_completed": False, "lap_time": None,
        "sector_completed": False, "sector_time": None,
        "current_sector": ct.current_sector,
        "elapsed_s": tick / ticks_per_sec,
    }
    if lap > ct._prev_lap and ct._prev_lap >= 0:
        result.update(_handle_lap_completion(ct, tick, ticks_per_sec))
    ct._prev_lap = lap
    if not result["lap_completed"]:
        result.update(_detect_sector(
            ct, distance_pct, tick, ticks_per_sec, sector_boundaries))
    result["current_sector"] = ct.current_sector
    return result


def get_fastest_lap(timings: dict[str, CarTiming]) -> tuple[str, float] | None:
    """Return (car_name, best_time) for fastest lap across all cars."""
    best_car, best_time = None, None
    for name, ct in timings.items():
        if ct.best_lap is not None and (best_time is None or ct.best_lap < best_time):
            best_car, best_time = name, ct.best_lap
    return (best_car, best_time) if best_car else None


def get_timing_summary(timings: dict[str, CarTiming]) -> list[dict]:
    """Return per-car timing summaries for results enrichment."""
    return [
        {"name": ct.name, "best_lap": ct.best_lap, "lap_times": ct.lap_times[:],
         "best_sectors": ct.best_sectors[:],
         "sector_times": [s[:] for s in ct.sector_times]}
        for ct in timings.values()
    ]
