"""Track listing endpoint."""

from fastapi import APIRouter

from tracks import TRACKS, list_tracks

router = APIRouter(prefix="/api", tags=["tracks"])


@router.get("/tracks")
async def get_tracks():
    """List all available tracks with metadata."""
    result = []
    for key in list_tracks():
        t = TRACKS[key]
        result.append({
            "name": key,
            "country": t["country"],
            "character": t["character"],
            "laps_default": t["laps_default"],
            "real_length_m": t.get("real_length_m"),
        })
    return {"tracks": result, "count": len(result)}
