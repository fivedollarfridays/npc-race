"""API key authentication for Code Circuit server."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from server.db import create_api_key, create_player, get_player_by_api_key, init_db


def get_db():
    """FastAPI dependency that provides a DB connection."""
    from server.config import settings

    conn = init_db(settings.db_path)
    try:
        yield conn
    finally:
        conn.close()


async def get_current_player(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    conn=Depends(get_db),
) -> dict:
    """Get current player from API key header.

    If no key provided, auto-create a player and key.
    Returns player dict with ``api_key`` field added when newly created.
    """
    if x_api_key:
        player = get_player_by_api_key(conn, x_api_key)
        if player is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return player

    # Auto-create player + key
    player = create_player(conn)
    key = create_api_key(conn, player["id"])
    player["api_key"] = key
    player["_new"] = True
    return player
