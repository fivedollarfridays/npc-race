"""Tests for T44.2 — arch decomposition, CORS, CAR_NAME validation, key hashing."""

import ast
import inspect

import pytest

from security.bot_scanner import scan_car_source


# --- Fix 1: parts_simulation function lengths ---


def _function_lengths(module) -> dict[str, int]:
    """Return {func_name: line_count} for all methods in a module's classes."""
    lengths = {}
    source = inspect.getsource(module)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = node.end_lineno - node.lineno + 1
            lengths[node.name] = length
    return lengths


def test_parts_sim_init_under_50_lines():
    """PartsRaceSim.__init__ must be under 50 lines after decomposition."""
    from engine import parts_simulation
    lengths = _function_lengths(parts_simulation)
    assert lengths["__init__"] <= 50, (
        f"__init__ is {lengths['__init__']} lines, must be <= 50"
    )


def test_parts_sim_step_under_50_lines():
    """PartsRaceSim.step must be under 50 lines after decomposition."""
    from engine import parts_simulation
    lengths = _function_lengths(parts_simulation)
    assert lengths["step"] <= 50, (
        f"step is {lengths['step']} lines, must be <= 50"
    )


def test_parts_sim_all_functions_under_50():
    """Every function in parts_simulation.py must be under 50 lines."""
    from engine import parts_simulation
    lengths = _function_lengths(parts_simulation)
    over = {k: v for k, v in lengths.items() if v > 50}
    assert not over, f"Functions over 50 lines: {over}"


# --- Fix 2: CORS tightening ---


def test_cors_explicit_methods():
    """CORS middleware must use explicit methods, not wildcard."""
    pytest.importorskip("fastapi")
    from server.app import app

    for mw in app.user_middleware:
        if "CORS" in str(mw.cls):
            methods = mw.kwargs.get("allow_methods", [])
            assert "*" not in methods, (
                f"CORS allow_methods must not contain '*', got {methods}"
            )
            assert "GET" in methods
            assert "POST" in methods


def test_cors_explicit_headers():
    """CORS middleware must use explicit headers, not wildcard."""
    pytest.importorskip("fastapi")
    from server.app import app

    for mw in app.user_middleware:
        if "CORS" in str(mw.cls):
            headers = mw.kwargs.get("allow_headers", [])
            assert "*" not in headers, (
                f"CORS allow_headers must not contain '*', got {headers}"
            )
            assert "Content-Type" in headers


def test_cors_origins_from_env(monkeypatch):
    """CORS origins should be configurable via CORS_ORIGINS env var."""
    monkeypatch.setenv("CORS_ORIGINS", "https://example.com,https://other.com")
    # Re-import to pick up env var
    from server.config import Settings
    s = Settings()
    assert "https://example.com" in s.cors_origins
    assert "https://other.com" in s.cors_origins


# --- Fix 3: CAR_NAME validation ---


_VALID_CAR_TEMPLATE = '''\
CAR_NAME = "{name}"
CAR_COLOR = "#ff0000"
POWER = 20
GRIP = 20
WEIGHT = 20
AERO = 20
BRAKES = 20

def strategy(state):
    return {{"throttle": 1.0}}
'''


def test_car_name_too_long_rejected():
    """CAR_NAME > 64 chars should produce a violation."""
    long_name = "A" * 65
    source = _VALID_CAR_TEMPLATE.format(name=long_name)
    result = scan_car_source(source)
    assert not result.passed
    assert any("too long" in v for v in result.violations), result.violations


def test_car_name_64_chars_accepted():
    """CAR_NAME of exactly 64 chars should be accepted."""
    name = "A" * 64
    source = _VALID_CAR_TEMPLATE.format(name=name)
    result = scan_car_source(source)
    # Should not have a name-length violation
    name_violations = [v for v in result.violations if "too long" in v]
    assert not name_violations, name_violations


def test_car_name_special_chars_rejected():
    """CAR_NAME with special characters (not alnum/underscore/dash) fails."""
    source = _VALID_CAR_TEMPLATE.format(name="my car!")
    result = scan_car_source(source)
    assert not result.passed
    assert any("alphanumeric" in v for v in result.violations), result.violations


def test_car_name_spaces_rejected():
    """CAR_NAME with spaces fails validation."""
    source = _VALID_CAR_TEMPLATE.format(name="my car")
    result = scan_car_source(source)
    assert not result.passed
    assert any("alphanumeric" in v for v in result.violations), result.violations


def test_car_name_valid_underscore_dash():
    """CAR_NAME with underscores and dashes is valid."""
    source = _VALID_CAR_TEMPLATE.format(name="my_car-v2")
    result = scan_car_source(source)
    assert result.passed, result.violations


# --- Fix 4: API key hashing ---


def test_api_key_stored_as_hash():
    """The raw API key should NOT appear in the api_keys table."""
    from server.db import create_api_key, create_player, init_db

    conn = init_db(":memory:")
    player = create_player(conn, "Tester")
    key = create_api_key(conn, player["id"])
    # Key should start with cc_
    assert key.startswith("cc_")
    # The raw key must NOT be in the table
    row = conn.execute(
        "SELECT key FROM api_keys WHERE player_id = ?", (player["id"],)
    ).fetchone()
    assert row is not None
    stored = row["key"]
    assert stored != key, "Raw API key stored in DB — must be hashed"


def test_api_key_lookup_succeeds_with_plaintext():
    """get_player_by_api_key should find a player using the plaintext key."""
    from server.db import (
        create_api_key, create_player, get_player_by_api_key, init_db,
    )

    conn = init_db(":memory:")
    player = create_player(conn, "Tester2")
    key = create_api_key(conn, player["id"])
    result = get_player_by_api_key(conn, key)
    assert result is not None
    assert result["id"] == player["id"]


def test_api_key_lookup_fails_with_hash():
    """Looking up the raw hash string should NOT find a player."""
    import hashlib
    from server.db import (
        create_api_key, create_player, get_player_by_api_key, init_db,
    )

    conn = init_db(":memory:")
    player = create_player(conn, "Tester3")
    key = create_api_key(conn, player["id"])
    # Compute hash the same way as db module should
    hashed = hashlib.sha256(key.encode()).hexdigest()
    # Looking up by hash directly should fail (double-hash)
    result = get_player_by_api_key(conn, hashed)
    assert result is None, "Lookup by hash should fail (would mean keys stored unhashed)"
