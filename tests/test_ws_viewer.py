"""Tests for WebSocket viewer client (T17.2)."""

import pathlib

MAIN_JS = pathlib.Path("viewer/js/main.js").read_text()


class TestWSClient:
    def test_ws_connection_code_in_main(self):
        assert "connectWebSocket" in MAIN_JS

    def test_ws_frame_handler(self):
        assert "handleWsFrame" in MAIN_JS

    def test_ws_init_handler(self):
        assert "handleWsInit" in MAIN_JS

    def test_ws_fallback(self):
        assert "fetch('replay.json')" in MAIN_JS or "fetch(\"replay.json\")" in MAIN_JS
