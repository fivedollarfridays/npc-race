"""Track listing endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from tracks import TRACKS, list_tracks

router = APIRouter(prefix="/api", tags=["tracks"])


class TrackResponse(BaseModel):
    """Response model for a single track."""

    name: str
    country: str
    character: str
    laps_default: int
    real_length_m: float | None = None


class TracksListResponse(BaseModel):
    """Response model for the tracks list endpoint."""

    tracks: list[TrackResponse]
    count: int


@router.get("/tracks", response_model=TracksListResponse)
async def get_tracks() -> TracksListResponse:
    """List all available tracks with metadata."""
    result = []
    for key in list_tracks():
        t = TRACKS[key]
        result.append(TrackResponse(
            name=key,
            country=t["country"],
            character=t["character"],
            laps_default=t["laps_default"],
            real_length_m=t.get("real_length_m"),
        ))
    return TracksListResponse(tracks=result, count=len(result))
