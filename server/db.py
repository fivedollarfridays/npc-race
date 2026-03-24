"""SQLite database for NPC Race server."""
import os
import sqlite3
import uuid
from datetime import datetime, timezone


def init_db(db_path: str = "data/npcrace.db") -> sqlite3.Connection:
    """Initialize database and create tables if needed."""
    if db_path != ":memory:":
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    _create_tables(conn)
    return conn


def _create_tables(conn: sqlite3.Connection) -> None:
    """Create players, api_keys, and cars tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS players (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            player_id TEXT NOT NULL REFERENCES players(id),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL REFERENCES players(id),
            name TEXT NOT NULL,
            color TEXT NOT NULL DEFAULT '#ffffff',
            source TEXT NOT NULL,
            league TEXT DEFAULT 'F3',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()


# --- CRUD operations ---


def create_player(conn: sqlite3.Connection, name: str = "Anonymous") -> dict:
    """Create a new player and return their data."""
    player_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO players (id, name, created_at) VALUES (?, ?, ?)",
        (player_id, name, now),
    )
    conn.commit()
    return {"id": player_id, "name": name, "created_at": now}


def get_player(conn: sqlite3.Connection, player_id: str) -> dict | None:
    """Get a player by ID, or None if not found."""
    row = conn.execute(
        "SELECT * FROM players WHERE id = ?", (player_id,)
    ).fetchone()
    return dict(row) if row else None


def create_api_key(conn: sqlite3.Connection, player_id: str) -> str:
    """Create an API key for a player and return it."""
    key = f"cc_{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO api_keys (key, player_id, created_at) VALUES (?, ?, ?)",
        (key, player_id, now),
    )
    conn.commit()
    return key


def get_player_by_api_key(conn: sqlite3.Connection, key: str) -> dict | None:
    """Look up a player by their API key, or None if invalid."""
    row = conn.execute(
        "SELECT p.* FROM players p JOIN api_keys k ON p.id = k.player_id WHERE k.key = ?",
        (key,),
    ).fetchone()
    return dict(row) if row else None


def store_car(
    conn: sqlite3.Connection,
    player_id: str,
    name: str,
    color: str,
    source: str,
    league: str = "F3",
) -> int:
    """Store a car and return its auto-generated ID."""
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO cars (player_id, name, color, source, league, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (player_id, name, color, source, league, now, now),
    )
    conn.commit()
    return cursor.lastrowid


def get_car(conn: sqlite3.Connection, car_id: int) -> dict | None:
    """Get a car by ID, or None if not found."""
    row = conn.execute("SELECT * FROM cars WHERE id = ?", (car_id,)).fetchone()
    return dict(row) if row else None


def get_player_cars(conn: sqlite3.Connection, player_id: str) -> list[dict]:
    """Get all cars for a player, newest first."""
    rows = conn.execute(
        "SELECT * FROM cars WHERE player_id = ? ORDER BY created_at DESC",
        (player_id,),
    ).fetchall()
    return [dict(r) for r in rows]
