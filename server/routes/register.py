"""Player registration endpoint."""

from fastapi import APIRouter, Depends

from server.auth import get_db
from server.db import create_api_key, create_player

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/register")
async def register(conn=Depends(get_db)):
    """Create a new player and return API key."""
    player = create_player(conn)
    key = create_api_key(conn, player["id"])
    return {"player_id": player["id"], "api_key": key}
