"""Tests for WebSocket live server (T17.1)."""

from engine.live_server import (
    stream_race, stream_replay, handler, start_server, DEFAULT_PORT,
)


class TestLiveServerAPI:
    def test_stream_race_function_exists(self):
        assert callable(stream_race)

    def test_stream_replay_function_exists(self):
        assert callable(stream_replay)

    def test_handler_function_exists(self):
        assert callable(handler)

    def test_start_server_function_exists(self):
        assert callable(start_server)

    def test_default_port(self):
        assert DEFAULT_PORT == 8766
