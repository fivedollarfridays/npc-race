"""Tests for track performance weights (T20.4)."""

from engine.track_performance import get_track_performance, TRACK_WEIGHTS
from engine.car_attributes import compute_attributes
from engine.parts_catalog import DEFAULTS
from tracks import list_tracks


class TestTrackPerformance:
    def test_monza_rewards_top_speed(self):
        slow = dict(DEFAULTS)
        slow["AERO"] = "aero_high_df"  # high drag = slower top speed
        fast = dict(DEFAULTS)
        fast["AERO"] = "aero_low_drag"  # low drag = faster top speed
        slow_perf = get_track_performance(compute_attributes(slow), "monza")
        fast_perf = get_track_performance(compute_attributes(fast), "monza")
        assert fast_perf < slow_perf  # lower = faster

    def test_monaco_rewards_grip(self):
        grippy = dict(DEFAULTS)
        grippy["SUSPENSION"] = "sus_soft"  # more mechanical grip
        stiff = dict(DEFAULTS)
        stiff["SUSPENSION"] = "sus_stiff"  # less mechanical grip
        assert get_track_performance(compute_attributes(grippy), "monaco") < \
               get_track_performance(compute_attributes(stiff), "monaco")

    def test_weights_sum_to_one(self):
        for track, w in TRACK_WEIGHTS.items():
            total = sum(w.values())
            assert 0.95 <= total <= 1.05, f"{track} weights sum to {total}"

    def test_all_tracks_have_weights(self):
        for track in list_tracks():
            assert track in TRACK_WEIGHTS, f"{track} missing weight profile"

    def test_performance_returns_float(self):
        attrs = compute_attributes(DEFAULTS)
        result = get_track_performance(attrs, "monza")
        assert isinstance(result, float)
