"""FastAPI application for NPC Race server."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from server.config import settings
from server.routes.analysis import router as analysis_router
from server.routes.cars import router as cars_router
from server.routes.health import router as health_router
from server.routes.lobby import router as lobby_router
from server.routes.submit import router as submit_router
from server.routes.tracks import router as tracks_router

app = FastAPI(title="Code Circuit", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router)
app.include_router(health_router)
app.include_router(submit_router)
app.include_router(cars_router)
app.include_router(tracks_router)
app.include_router(lobby_router)

# Mount static directories
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
app.mount("/viewer", StaticFiles(directory=settings.viewer_dir), name="viewer")
