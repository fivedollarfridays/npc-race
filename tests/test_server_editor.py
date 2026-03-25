"""Tests for the car editor page with Monaco + submit flow."""

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from server.app import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def editor_html(client):
    """Fetch editor page once for reuse."""
    r = client.get("/static/editor.html")
    assert r.status_code == 200
    return r.text


def test_editor_page_loads(client):
    """Editor page loads and contains Monaco script tag."""
    r = client.get("/static/editor.html")
    assert r.status_code == 200
    assert "monaco" in r.text.lower()


def test_editor_has_monaco_cdn(editor_html):
    """Editor loads Monaco from CDN."""
    assert "monaco-editor" in editor_html
    assert "loader.js" in editor_html


def test_editor_has_submit_button(editor_html):
    """Editor has a submit button."""
    assert "Submit" in editor_html or "submit" in editor_html


def test_editor_has_template_code(editor_html):
    """Editor includes car template with CAR_NAME."""
    assert "CAR_NAME" in editor_html


def test_editor_has_strategy_function(editor_html):
    """Editor template includes a strategy function."""
    assert "def strategy" in editor_html


def test_editor_has_lobby_status(editor_html):
    """Editor includes lobby status area."""
    assert "lobby" in editor_html.lower()


def test_editor_has_dark_theme(editor_html):
    """Editor uses the dark theme CSS variables."""
    assert "--bg" in editor_html
    assert "--accent" in editor_html


def test_editor_has_status_panel(editor_html):
    """Editor has a status panel for errors and lobby info."""
    assert "status" in editor_html.lower()


def test_editor_has_api_submit_call(editor_html):
    """Editor JS calls the submit-car API."""
    assert "/api/submit-car" in editor_html


def test_editor_has_lobby_join_call(editor_html):
    """Editor JS calls the lobby join API."""
    assert "/api/lobby/join" in editor_html


def test_editor_has_lobby_status_poll(editor_html):
    """Editor JS polls lobby status endpoint."""
    assert "/api/lobby/status" in editor_html


def test_editor_has_parts_panel(editor_html):
    """Editor has a parts detection panel."""
    assert "parts-panel" in editor_html
    assert "parts-grid" in editor_html


def test_editor_has_league_indicator(editor_html):
    """Editor has a league badge indicator."""
    assert "league-badge" in editor_html
    assert "league-panel" in editor_html


def test_editor_has_quality_meter(editor_html):
    """Editor has a code quality meter."""
    assert "quality-panel" in editor_html
    assert "quality-bar" in editor_html
    assert "Reliability" in editor_html


def test_editor_has_analyze_code_function(editor_html):
    """Editor JS has analyzeCode function calling /api/car-analysis."""
    assert "analyzeCode" in editor_html
    assert "/api/car-analysis" in editor_html


def test_editor_has_debounced_analysis(editor_html):
    """Editor debounces analysis on content change."""
    assert "analyzeTimeout" in editor_html
    assert "setTimeout" in editor_html
