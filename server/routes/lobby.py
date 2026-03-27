"""Lobby API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from server.rate_limit import limiter
from server.auth import get_current_player, get_db
from server.db import get_car
from server.lobby import Lobby, LobbyClosedError, LobbyDuplicateError, LobbyFullError

router = APIRouter(prefix="/api", tags=["lobby"])

# Global lobby instance
_current_lobby = Lobby()


def _get_lobby() -> Lobby:
    """Get the current lobby, checking trigger state."""
    global _current_lobby
    _current_lobby.check_trigger()
    return _current_lobby


def reset_lobby() -> None:
    """Create a fresh lobby (called after race starts or for testing)."""
    global _current_lobby
    _current_lobby = Lobby()


class JoinRequest(BaseModel):
    """Request body for joining a lobby."""

    car_id: str


@router.post("/lobby/join")
@limiter.limit("5/minute")
async def join_lobby(
    request: Request,
    req: JoinRequest,
    player=Depends(get_current_player),
    conn=Depends(get_db),
) -> dict:
    """Join the current lobby with a submitted car."""
    car = get_car(conn, req.car_id)
    if not car:
        raise HTTPException(404, detail="Car not found")
    if car["player_id"] != player["id"]:
        raise HTTPException(403, detail="Not your car")

    lobby = _get_lobby()
    car_config = {
        "car_id": car["id"],
        "player_id": player["id"],
        "name": car["name"],
        "color": car["color"],
        "source": car["source"],
    }

    try:
        status = lobby.join(car_config)
    except LobbyFullError:
        raise HTTPException(409, detail="Lobby is full")
    except LobbyClosedError:
        raise HTTPException(409, detail="Lobby already started")
    except LobbyDuplicateError:
        raise HTTPException(409, detail="Already in lobby")

    response: dict = {"status": "joined", **status}
    if player.get("_new"):
        response["api_key"] = player["api_key"]
    return response


@router.get("/lobby/status")
async def lobby_status() -> dict:
    """Get current lobby state (public, no auth required)."""
    lobby = _get_lobby()
    return lobby.status()
