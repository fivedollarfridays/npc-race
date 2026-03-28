"""Game frame endpoint for embedding in agentgrounds.ai CRT monitor."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/api/game-frame")
async def game_frame() -> RedirectResponse:
    """Redirect to editor in embedded mode for CRT frame embedding."""
    return RedirectResponse(url="/static/editor.html?embed=true")
