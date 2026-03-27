"""API key authentication for Code Circuit server."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from server.db import get_player_by_api_key, init_db


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

    Requires a valid API key. Use POST /api/register to obtain one.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required. POST /api/register to get one.",
        )
    player = get_player_by_api_key(conn, x_api_key)
    if player is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return player
