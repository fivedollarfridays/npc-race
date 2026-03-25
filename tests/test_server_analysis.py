"""Tests for POST /api/car-analysis endpoint."""

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


# --- Part detection ---


def test_analysis_detects_strategy():
    """Source with def strategy() shows strategy detected."""
    source = 'def strategy(state): return {}'
    resp = client.post("/api/car-analysis", json={"source": source})
    assert resp.status_code == 200
    parts = {p["name"]: p["detected"] for p in resp.json()["parts"]}
    assert parts["strategy"] is True


def test_analysis_detects_multiple_parts():
    """Source with multiple known parts detects them all."""
    source = (
        "def gearbox(state): return 3\n"
        "def cooling(state): return 0.5\n"
        "def strategy(state): return {}\n"
    )
    resp = client.post("/api/car-analysis", json={"source": source})
    parts = {p["name"]: p["detected"] for p in resp.json()["parts"]}
    assert parts["gearbox"] is True
    assert parts["cooling"] is True
    assert parts["strategy"] is True
    assert parts["engine_map"] is False


def test_analysis_empty_source():
    """Empty source returns all parts undetected."""
    resp = client.post("/api/car-analysis", json={"source": ""})
    assert resp.status_code == 200
    parts = resp.json()["parts"]
    assert len(parts) == 10
    assert all(p["detected"] is False for p in parts)


def test_analysis_syntax_error_source():
    """Source with syntax errors returns all parts undetected."""
    resp = client.post("/api/car-analysis", json={"source": "def ("})
    parts = resp.json()["parts"]
    assert all(p["detected"] is False for p in parts)


# --- League detection ---


def test_analysis_league_f3():
    """F3 parts only -> league F3."""
    source = (
        "def gearbox(state): return 3\n"
        "def cooling(state): return 0.5\n"
        "def strategy(state): return {}\n"
    )
    resp = client.post("/api/car-analysis", json={"source": source})
    assert resp.json()["league"] == "F3"


def test_analysis_league_f2():
    """F2 parts -> league F2."""
    source = (
        "def gearbox(s): pass\n"
        "def cooling(s): pass\n"
        "def strategy(s): pass\n"
        "def suspension(s): pass\n"
        "def ers_deploy(s): pass\n"
        "def fuel_mix(s): pass\n"
    )
    resp = client.post("/api/car-analysis", json={"source": source})
    assert resp.json()["league"] == "F2"


def test_analysis_league_championship():
    """All 10 parts -> Championship league."""
    parts = [
        "engine_map", "gearbox", "fuel_mix", "suspension", "cooling",
        "ers_deploy", "differential", "brake_bias", "ers_harvest", "strategy",
    ]
    source = "\n".join(f"def {p}(s): pass" for p in parts)
    resp = client.post("/api/car-analysis", json={"source": source})
    assert resp.json()["league"] == "Championship"


# --- Code quality ---


def test_analysis_quality_simple_code():
    """Simple code has high reliability."""
    source = "def strategy(state): return {}"
    resp = client.post("/api/car-analysis", json={"source": source})
    quality = resp.json()["quality"]
    assert "reliability" in quality
    assert quality["reliability"] >= 0.9


def test_analysis_quality_has_complexity():
    """Quality response includes complexity dict."""
    source = "def strategy(state): return {}"
    resp = client.post("/api/car-analysis", json={"source": source})
    quality = resp.json()["quality"]
    assert "complexity" in quality
