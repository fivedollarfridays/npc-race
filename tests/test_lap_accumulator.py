"""Tests for engine.lap_accumulator — LapAccumulator class."""

import pytest

from engine.lap_accumulator import LapAccumulator


# ---- Cycle 1: empty accumulator ----

def test_empty_accumulator_lap_summaries():
    acc = LapAccumulator()
    assert acc.get_lap_summaries() == {}


def test_empty_accumulator_race_summary():
    acc = LapAccumulator()
    summary = acc.get_race_summary()
    assert summary == {}


# ---- Helpers ----

def _make_state(name: str, position: int = 1, compound: str = "medium",
                tire_wear: float = 0.1, fuel_kg: float = 50.0,
                pit_status: str = "racing") -> dict:
    """Build a minimal car state dict matching RaceSim format."""
    return {
        "name": name,
        "tire_compound": compound,
        "tire_wear": tire_wear,
        "fuel_kg": fuel_kg,
        "max_fuel_kg": 80.0,
        "pit_state": {"status": pit_status, "pit_stops": 0},
    }


def _positions(names: list[str]) -> dict[str, int]:
    """Build a positions dict: {name: 1-indexed position}."""
    return {n: i + 1 for i, n in enumerate(names)}


# ---- Cycle 2: single car, 3 laps ----

def test_single_car_three_laps():
    acc = LapAccumulator()
    car = "Alpha"

    # Simulate 3 laps: tick some state, then complete each lap
    for lap_num in range(1, 4):
        wear = 0.1 * lap_num
        fuel = 80.0 - 10.0 * lap_num
        state = _make_state(car, compound="medium", tire_wear=wear,
                            fuel_kg=fuel)
        acc.on_tick([state], _positions([car]), tick=lap_num * 100)
        acc.on_lap_complete(car, lap=lap_num, lap_time=80.0 + lap_num)

    summaries = acc.get_lap_summaries()
    assert car in summaries
    assert len(summaries[car]) == 3

    lap1 = summaries[car][0]
    assert lap1["lap"] == 1
    assert lap1["time_s"] == 81.0
    assert lap1["position"] == 1
    assert lap1["tire_compound"] == "medium"
    assert lap1["tire_wear"] == pytest.approx(0.1)
    assert lap1["fuel_remaining_pct"] == pytest.approx(70.0 / 80.0)
    assert lap1["pit_stop"] is False

    lap3 = summaries[car][2]
    assert lap3["lap"] == 3
    assert lap3["time_s"] == 83.0
    assert lap3["tire_wear"] == pytest.approx(0.3)


def test_position_tracked_at_lap_end():
    """Position at lap end should reflect last on_tick positions."""
    acc = LapAccumulator()
    a = _make_state("A")
    b = _make_state("B")

    # Tick with A in P1
    acc.on_tick([a, b], _positions(["A", "B"]), tick=50)
    # Then B overtakes
    acc.on_tick([a, b], _positions(["B", "A"]), tick=100)

    acc.on_lap_complete("A", lap=1, lap_time=80.0)
    acc.on_lap_complete("B", lap=1, lap_time=79.5)

    assert acc.get_lap_summaries()["A"][0]["position"] == 2
    assert acc.get_lap_summaries()["B"][0]["position"] == 1


# ---- Cycle 3: pit stop detection ----

def test_pit_stop_detected():
    """pit_stop=True when pit_state transitions from racing to non-racing."""
    acc = LapAccumulator()
    car = "Bravo"
    pos = _positions([car])

    # Tick 1: racing normally
    acc.on_tick([_make_state(car, pit_status="racing")], pos, tick=10)
    # Tick 2: entered pit
    acc.on_tick([_make_state(car, pit_status="pit_entry")], pos, tick=20)
    # Tick 3: stationary in pit
    acc.on_tick([_make_state(car, pit_status="pit_stationary")], pos, tick=30)
    # Tick 4: back to racing
    acc.on_tick([_make_state(car, pit_status="racing")], pos, tick=40)

    acc.on_lap_complete(car, lap=1, lap_time=90.0)

    entry = acc.get_lap_summaries()[car][0]
    assert entry["pit_stop"] is True


def test_no_pit_stop_when_always_racing():
    """pit_stop=False when car never leaves racing status."""
    acc = LapAccumulator()
    car = "Charlie"
    pos = _positions([car])

    for t in range(1, 4):
        acc.on_tick([_make_state(car, pit_status="racing")], pos, tick=t * 10)

    acc.on_lap_complete(car, lap=1, lap_time=82.0)
    assert acc.get_lap_summaries()[car][0]["pit_stop"] is False


def test_pit_stop_resets_between_laps():
    """Pit flag resets per lap -- pitting in lap 1 does not bleed to lap 2."""
    acc = LapAccumulator()
    car = "Delta"
    pos = _positions([car])

    # Lap 1: pit stop
    acc.on_tick([_make_state(car, pit_status="racing")], pos, tick=10)
    acc.on_tick([_make_state(car, pit_status="pit_entry")], pos, tick=20)
    acc.on_tick([_make_state(car, pit_status="racing")], pos, tick=30)
    acc.on_lap_complete(car, lap=1, lap_time=95.0)

    # Lap 2: no pit stop
    acc.on_tick([_make_state(car, pit_status="racing")], pos, tick=40)
    acc.on_tick([_make_state(car, pit_status="racing")], pos, tick=50)
    acc.on_lap_complete(car, lap=2, lap_time=82.0)

    assert acc.get_lap_summaries()[car][0]["pit_stop"] is True
    assert acc.get_lap_summaries()[car][1]["pit_stop"] is False


# ---- Cycle 4: tire compound change ----

def test_tire_compound_change_recorded():
    """Compound should reflect the latest value at lap end."""
    acc = LapAccumulator()
    car = "Echo"
    pos = _positions([car])

    # Lap 1 on medium
    acc.on_tick([_make_state(car, compound="medium")], pos, tick=10)
    acc.on_lap_complete(car, lap=1, lap_time=80.0)

    # Lap 2: pit stop changes to hard
    acc.on_tick([_make_state(car, compound="medium", pit_status="pit_entry")],
                pos, tick=20)
    acc.on_tick([_make_state(car, compound="hard", pit_status="racing")],
                pos, tick=30)
    acc.on_lap_complete(car, lap=2, lap_time=85.0)

    laps = acc.get_lap_summaries()[car]
    assert laps[0]["tire_compound"] == "medium"
    assert laps[1]["tire_compound"] == "hard"


# ---- Cycle 5: race summary ----

def test_race_summary_aggregates():
    """get_race_summary should aggregate lap data per car."""
    acc = LapAccumulator()
    car = "Fox"
    pos = _positions([car])

    # 3 laps
    for lap_num in range(1, 4):
        acc.on_tick([_make_state(car)], pos, tick=lap_num * 100)
        acc.on_lap_complete(car, lap=lap_num, lap_time=80.0 + lap_num)

    summary = acc.get_race_summary()
    assert car in summary
    assert summary[car]["total_laps"] == 3
    assert summary[car]["total_time_s"] == pytest.approx(81.0 + 82.0 + 83.0)
    assert summary[car]["best_lap_s"] == pytest.approx(81.0)
    assert summary[car]["avg_lap_s"] == pytest.approx(246.0 / 3)
    assert summary[car]["pit_stops"] == 0
    assert summary[car]["final_position"] == 1
