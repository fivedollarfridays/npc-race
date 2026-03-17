"""Tests for engine/pit_lane.py -- pit stop state machine."""

from engine.pit_lane import (
    PIT_ENTRY_TICKS,
    PIT_EXIT_TICKS,
    PIT_STOP_TICKS,
    PIT_SPEED_LIMIT,
    complete_pit_stop,
    create_pit_state,
    get_speed_limit,
    is_in_pit,
    request_pit_stop,
    update_pit_state,
)


class TestCreatePitState:
    """Cycle 1: create_pit_state returns correct defaults."""

    def test_returns_dict(self):
        state = create_pit_state()
        assert isinstance(state, dict)

    def test_default_status_is_racing(self):
        state = create_pit_state()
        assert state["status"] == "racing"

    def test_default_pit_timer_is_zero(self):
        state = create_pit_state()
        assert state["pit_timer"] == 0

    def test_default_pit_stops_is_zero(self):
        state = create_pit_state()
        assert state["pit_stops"] == 0

    def test_default_requested_compound_is_none(self):
        state = create_pit_state()
        assert state["requested_compound"] is None

    def test_default_pending_request_is_false(self):
        state = create_pit_state()
        assert state["pending_request"] is False


class TestRequestPitStop:
    """Cycle 2: request_pit_stop queues when racing, rejects when in pit."""

    def test_request_while_racing_sets_pending(self):
        state = create_pit_state()
        result = request_pit_stop(state, "soft")
        assert result["pending_request"] is True

    def test_request_while_racing_sets_compound(self):
        state = create_pit_state()
        result = request_pit_stop(state, "hard")
        assert result["requested_compound"] == "hard"

    def test_request_while_in_pit_entry_ignored(self):
        state = create_pit_state()
        state["status"] = "pit_entry"
        result = request_pit_stop(state, "soft")
        assert result["pending_request"] is False

    def test_request_while_stationary_ignored(self):
        state = create_pit_state()
        state["status"] = "pit_stationary"
        result = request_pit_stop(state, "soft")
        assert result["pending_request"] is False

    def test_request_while_pit_exit_ignored(self):
        state = create_pit_state()
        state["status"] = "pit_exit"
        result = request_pit_stop(state, "medium")
        assert result["pending_request"] is False

    def test_does_not_mutate_input(self):
        state = create_pit_state()
        request_pit_stop(state, "soft")
        assert state["pending_request"] is False


class TestUpdatePitStateTransitions:
    """Cycle 3: update_pit_state drives the state machine."""

    def test_pending_request_transitions_to_pit_entry(self):
        state = create_pit_state()
        state = request_pit_stop(state, "soft")
        state, completed = update_pit_state(state)
        assert state["status"] == "pit_entry"
        assert state["pit_timer"] == PIT_ENTRY_TICKS
        assert state["pending_request"] is False
        assert completed is False

    def test_racing_without_request_stays_racing(self):
        state = create_pit_state()
        state, completed = update_pit_state(state)
        assert state["status"] == "racing"
        assert completed is False

    def test_pit_entry_decrements_timer(self):
        state = create_pit_state()
        state["status"] = "pit_entry"
        state["pit_timer"] = 5
        state, _ = update_pit_state(state)
        assert state["pit_timer"] == 4
        assert state["status"] == "pit_entry"

    def test_pit_entry_transitions_to_stationary_at_zero(self):
        state = create_pit_state()
        state["status"] = "pit_entry"
        state["pit_timer"] = 1
        state, completed = update_pit_state(state)
        assert state["status"] == "pit_stationary"
        assert state["pit_timer"] == PIT_STOP_TICKS
        assert completed is False

    def test_pit_stationary_transitions_to_exit_at_zero(self):
        state = create_pit_state()
        state["status"] = "pit_stationary"
        state["pit_timer"] = 1
        state, completed = update_pit_state(state)
        assert state["status"] == "pit_exit"
        assert state["pit_timer"] == PIT_EXIT_TICKS
        assert completed is False

    def test_pit_exit_transitions_to_racing_at_zero(self):
        state = create_pit_state()
        state["status"] = "pit_exit"
        state["pit_timer"] = 1
        state, completed = update_pit_state(state)
        assert state["status"] == "racing"
        assert completed is True


class TestUpdatePitStateDurations:
    """Cycle 3b: verify each phase lasts the correct number of ticks."""

    def test_pit_entry_lasts_correct_ticks(self):
        state = create_pit_state()
        state = request_pit_stop(state, "soft")
        ticks = 0
        while state["status"] != "pit_stationary":
            state, _ = update_pit_state(state)
            ticks += 1
        # 1 tick for racing->pit_entry + PIT_ENTRY_TICKS to drain timer
        assert ticks == 1 + PIT_ENTRY_TICKS

    def test_pit_stationary_lasts_correct_ticks(self):
        state = create_pit_state()
        state["status"] = "pit_stationary"
        state["pit_timer"] = PIT_STOP_TICKS
        ticks = 0
        while state["status"] == "pit_stationary":
            state, _ = update_pit_state(state)
            ticks += 1
        assert ticks == PIT_STOP_TICKS

    def test_pit_exit_lasts_correct_ticks(self):
        state = create_pit_state()
        state["status"] = "pit_exit"
        state["pit_timer"] = PIT_EXIT_TICKS
        ticks = 0
        while state["status"] == "pit_exit":
            state, _ = update_pit_state(state)
            ticks += 1
        assert ticks == PIT_EXIT_TICKS

    def test_full_cycle_racing_to_racing(self):
        """Full pit stop cycle: racing -> entry -> stationary -> exit -> racing."""
        state = create_pit_state()
        state = request_pit_stop(state, "medium")
        completed_count = 0
        ticks = 0
        max_ticks = PIT_ENTRY_TICKS + PIT_STOP_TICKS + PIT_EXIT_TICKS + 10
        while ticks < max_ticks:
            state, completed = update_pit_state(state)
            ticks += 1
            if completed:
                completed_count += 1
                break
        assert completed_count == 1
        assert state["status"] == "racing"
        # 1 tick racing->entry + entry + stop + exit ticks
        expected = 1 + PIT_ENTRY_TICKS + PIT_STOP_TICKS + PIT_EXIT_TICKS
        assert ticks == expected


class TestIsInPit:
    """Cycle 4: is_in_pit returns correct values for each status."""

    def test_racing_is_not_in_pit(self):
        state = create_pit_state()
        assert is_in_pit(state) is False

    def test_pit_entry_is_in_pit(self):
        state = create_pit_state()
        state["status"] = "pit_entry"
        assert is_in_pit(state) is True

    def test_pit_stationary_is_in_pit(self):
        state = create_pit_state()
        state["status"] = "pit_stationary"
        assert is_in_pit(state) is True

    def test_pit_exit_is_in_pit(self):
        state = create_pit_state()
        state["status"] = "pit_exit"
        assert is_in_pit(state) is True


class TestGetSpeedLimit:
    """Cycle 4b: speed limit during entry/exit, None otherwise."""

    def test_racing_no_speed_limit(self):
        state = create_pit_state()
        assert get_speed_limit(state) is None

    def test_pit_entry_has_speed_limit(self):
        state = create_pit_state()
        state["status"] = "pit_entry"
        assert get_speed_limit(state) == PIT_SPEED_LIMIT

    def test_pit_exit_has_speed_limit(self):
        state = create_pit_state()
        state["status"] = "pit_exit"
        assert get_speed_limit(state) == PIT_SPEED_LIMIT

    def test_pit_stationary_no_speed_limit(self):
        state = create_pit_state()
        state["status"] = "pit_stationary"
        assert get_speed_limit(state) is None


class TestCompletePitStop:
    """Cycle 5: complete_pit_stop increments counter and returns compound."""

    def test_increments_pit_stops(self):
        state = create_pit_state()
        state["requested_compound"] = "soft"
        result, _ = complete_pit_stop(state)
        assert result["pit_stops"] == 1

    def test_returns_requested_compound(self):
        state = create_pit_state()
        state["requested_compound"] = "hard"
        _, compound = complete_pit_stop(state)
        assert compound == "hard"

    def test_clears_requested_compound(self):
        state = create_pit_state()
        state["requested_compound"] = "soft"
        result, _ = complete_pit_stop(state)
        assert result["requested_compound"] is None

    def test_second_pit_stop_increments_to_two(self):
        state = create_pit_state()
        state["pit_stops"] = 1
        state["requested_compound"] = "medium"
        result, _ = complete_pit_stop(state)
        assert result["pit_stops"] == 2

    def test_does_not_mutate_input(self):
        state = create_pit_state()
        state["requested_compound"] = "soft"
        complete_pit_stop(state)
        assert state["pit_stops"] == 0
