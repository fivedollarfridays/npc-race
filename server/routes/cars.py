"""Car management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from server.auth import get_current_player, get_db
from server.db import get_car, get_player_cars

router = APIRouter(prefix="/api", tags=["cars"])


class CarSummary(BaseModel):
    """Summary model for car list items."""

    id: str
    name: str
    color: str
    league: str
    created_at: str


class CarListResponse(BaseModel):
    """Response model for the cars list endpoint."""

    cars: list[CarSummary]


class CarDetailResponse(BaseModel):
    """Response model for car detail endpoint."""

    id: str
    player_id: str
    name: str
    color: str
    source: str
    league: str
    created_at: str
    updated_at: str


@router.get("/cars", response_model=CarListResponse)
async def list_cars(
    player=Depends(get_current_player), conn=Depends(get_db)
) -> CarListResponse:
    """List current player's submitted cars."""
    cars = get_player_cars(conn, player["id"])
    return CarListResponse(
        cars=[
            CarSummary(
                id=c["id"],
                name=c["name"],
                color=c["color"],
                league=c["league"],
                created_at=c["created_at"],
            )
            for c in cars
        ]
    )


@router.get("/cars/{car_id}", response_model=CarDetailResponse)
async def get_car_detail(
    car_id: str,
    player=Depends(get_current_player),
    conn=Depends(get_db),
) -> CarDetailResponse:
    """Get car details by ID (requires auth + ownership)."""
    car = get_car(conn, car_id)
    if not car or car["player_id"] != player["id"]:
        raise HTTPException(404, detail="Car not found")
    return CarDetailResponse(**dict(car))
