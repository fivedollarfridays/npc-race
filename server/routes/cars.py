"""Car management endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from server.auth import get_current_player, get_db
from server.db import get_car, get_player_cars

router = APIRouter(prefix="/api", tags=["cars"])


@router.get("/cars")
async def list_cars(
    player=Depends(get_current_player), conn=Depends(get_db)
):
    """List current player's submitted cars."""
    cars = get_player_cars(conn, player["id"])
    return {
        "cars": [
            {
                "id": c["id"],
                "name": c["name"],
                "color": c["color"],
                "league": c["league"],
                "created_at": c["created_at"],
            }
            for c in cars
        ]
    }


@router.get("/cars/{car_id}")
async def get_car_detail(
    car_id: int,
    player=Depends(get_current_player),
    conn=Depends(get_db),
):
    """Get car details by ID (requires auth + ownership)."""
    car = get_car(conn, car_id)
    if not car or car["player_id"] != player["id"]:
        raise HTTPException(404, detail="Car not found")
    return dict(car)
