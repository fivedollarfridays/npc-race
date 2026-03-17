"""Tests for replay v2 — new physics fields in per-car frame data."""

from engine.replay import record_frame, export_replay


def _make_track():
    """Return a simple square track with precomputed distances."""
    track = [(0, 0), (100, 0), (100, 100), (0, 100)]
    distances = [0.0, 100.0, 200.0, 300.0]
    track_length = 400.0
    track_width = 50
    return track, distances, track_length, track_width


def _make_state(overrides=None):
    """Build a minimal car state dict with all fields."""
    state = {
        "car_idx": 0,
        "name": "TestCar",
        "color": "#ff0000",
        "speed": 80.0,
        "lap": 1,
        "distance": 50.0,
        "lateral": 0.3,
        "tire_wear": 0.15,
        "boost_active": 0,
        "finished": False,
        "tire_compound": "soft",
        "fuel_kg": 30.0,
        "max_fuel_kg": 60.0,
        "pit_state": {"status": "pit_entry", "pit_stops": 1},
        "engine_mode": "push",
    }
    if overrides:
        state.update(overrides)
    return state


def _record_single(state_overrides=None):
    """Record a single-car frame and return the car entry dict."""
    track, distances, track_length, track_width = _make_track()
    state = _make_state(state_overrides)
    positions = {0: 1}
    frame = record_frame(
        states=[state],
        positions=positions,
        track=track,
        distances=distances,
        track_length=track_length,
        track_width=track_width,
    )
    return frame[0]


class TestNewFrameFields:
    """New physics fields must appear in recorded frame data."""

    def test_tire_compound_present(self):
        entry = _record_single()
        assert "tire_compound" in entry
        assert entry["tire_compound"] == "soft"

    def test_fuel_pct_present(self):
        entry = _record_single()
        assert "fuel_pct" in entry
        assert entry["fuel_pct"] == 0.5  # 30/60

    def test_pit_status_present(self):
        entry = _record_single()
        assert "pit_status" in entry
        assert entry["pit_status"] == "pit_entry"

    def test_engine_mode_present(self):
        entry = _record_single()
        assert "engine_mode" in entry
        assert entry["engine_mode"] == "push"

    def test_lateral_present(self):
        entry = _record_single()
        assert "lateral" in entry
        assert entry["lateral"] == 0.3


class TestFuelPctCalculation:
    """fuel_pct should be fuel_kg / max_fuel_kg, rounded to 2 decimals."""

    def test_full_fuel(self):
        entry = _record_single({"fuel_kg": 60.0, "max_fuel_kg": 60.0})
        assert entry["fuel_pct"] == 1.0

    def test_empty_fuel(self):
        entry = _record_single({"fuel_kg": 0.0, "max_fuel_kg": 60.0})
        assert entry["fuel_pct"] == 0.0

    def test_partial_fuel_rounded(self):
        # 20/60 = 0.33333... -> 0.33
        entry = _record_single({"fuel_kg": 20.0, "max_fuel_kg": 60.0})
        assert entry["fuel_pct"] == 0.33

    def test_zero_max_fuel_no_crash(self):
        """max_fuel_kg=0 should not cause division by zero."""
        entry = _record_single({"fuel_kg": 0.0, "max_fuel_kg": 0.0})
        assert entry["fuel_pct"] == 0.0


class TestBackwardCompatibility:
    """Old state dicts without new fields must not crash."""

    def _make_old_state(self):
        return {
            "car_idx": 0,
            "name": "OldCar",
            "color": "#00ff00",
            "speed": 60.0,
            "lap": 0,
            "distance": 10.0,
            "lateral": 0.0,
            "tire_wear": 0.0,
            "boost_active": 0,
            "finished": False,
            # No tire_compound, fuel_kg, max_fuel_kg, pit_state, engine_mode
        }

    def test_old_state_no_crash(self):
        track, distances, track_length, track_width = _make_track()
        state = self._make_old_state()
        positions = {0: 1}
        frame = record_frame(
            states=[state],
            positions=positions,
            track=track,
            distances=distances,
            track_length=track_length,
            track_width=track_width,
        )
        assert len(frame) == 1

    def test_old_state_defaults(self):
        track, distances, track_length, track_width = _make_track()
        state = self._make_old_state()
        positions = {0: 1}
        frame = record_frame(
            states=[state],
            positions=positions,
            track=track,
            distances=distances,
            track_length=track_length,
            track_width=track_width,
        )
        entry = frame[0]
        assert entry["tire_compound"] == "medium"
        assert entry["fuel_pct"] == 0.0
        assert entry["pit_status"] == "racing"
        assert entry["engine_mode"] == "standard"
        assert entry["lateral"] == 0.0


class TestExportReplayWithNewFields:
    """export_replay should pass through frames containing new fields."""

    def test_export_with_enriched_frames(self):
        entry = _record_single()
        replay = export_replay(
            track=[(0, 0), (100, 0)],
            track_width=50,
            track_name="test",
            laps=1,
            ticks_per_sec=30,
            history=[[entry]],
            states=[],
            num_cars=1,
        )
        frame_entry = replay["frames"][0][0]
        for key in ("tire_compound", "fuel_pct", "pit_status",
                     "engine_mode", "lateral"):
            assert key in frame_entry, f"Missing key in export: {key}"
