"""Tests for the landing page and editor stub."""

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from server.app import app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)


def test_landing_page_loads(client):
    r = client.get("/static/index.html")
    assert r.status_code == 200
    assert "CODE CIRCUIT" in r.text


def test_landing_has_editor_link(client):
    r = client.get("/static/index.html")
    assert "editor.html" in r.text


def test_landing_has_build_button(client):
    r = client.get("/static/index.html")
    assert "BUILD YOUR CAR" in r.text


def test_landing_has_tagline(client):
    r = client.get("/static/index.html")
    assert "Write Python" in r.text


def test_landing_has_css_variables(client):
    r = client.get("/static/index.html")
    assert "--accent" in r.text
    assert "--bg" in r.text


def test_editor_stub_loads(client):
    r = client.get("/static/editor.html")
    assert r.status_code == 200
    assert "Car Editor" in r.text


def test_editor_stub_has_back_link(client):
    r = client.get("/static/editor.html")
    assert "index.html" in r.text
