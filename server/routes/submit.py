"""Car submission endpoint."""

import ast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from server.rate_limit import limiter
from server.auth import get_current_player, get_db
from server.db import store_car
from security.bot_scanner import scan_car_source

router = APIRouter(prefix="/api", tags=["cars"])

MAX_SOURCE_BYTES = 32768  # 32KB


class CarSubmission(BaseModel):
    source: str = Field(..., max_length=MAX_SOURCE_BYTES)


class CarResponse(BaseModel):
    car_id: int
    name: str
    color: str
    league: str


@router.post("/submit-car", response_model=CarResponse)
@limiter.limit("10/minute")
async def submit_car(
    request: Request,
    submission: CarSubmission,
    player=Depends(get_current_player),
    conn=Depends(get_db),
):
    """Submit car source code for validation and storage."""
    source = submission.source.strip()
    if not source:
        raise HTTPException(400, detail="Empty source code")
    if len(source) > MAX_SOURCE_BYTES:
        raise HTTPException(400, detail="Source code too large (max 32KB)")

    # Security scan
    result = scan_car_source(source)
    if not result.passed:
        raise HTTPException(400, detail={"errors": result.violations})

    # Extract CAR_NAME and CAR_COLOR from AST
    name, color = _extract_car_metadata(source)
    if not name:
        raise HTTPException(400, detail="Missing CAR_NAME assignment")

    # Store in DB
    car_id = store_car(conn, player["id"], name, color or "#ffffff", source)

    return {
        "car_id": car_id,
        "name": name,
        "color": color or "#ffffff",
        "league": "F3",
    }


def _extract_car_metadata(source: str) -> tuple[str | None, str | None]:
    """Extract CAR_NAME and CAR_COLOR from source AST."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, None

    name = color = None
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and isinstance(
                node.value, ast.Constant
            ):
                if target.id == "CAR_NAME":
                    name = node.value.value
                elif target.id == "CAR_COLOR":
                    color = node.value.value
    return name, color
