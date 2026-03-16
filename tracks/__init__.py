"""Tracks package — 20 named track presets for NPC Race.

Usage:
    from tracks import TRACKS, get_track, list_tracks, random_track
"""

import random as _random

from .power import POWER_TRACKS
from .technical import TECHNICAL_TRACKS
from .balanced import BALANCED_TRACKS
from .character import CHARACTER_TRACKS

# Merge all track dicts into one
TRACKS: dict[str, dict] = {
    **POWER_TRACKS,
    **TECHNICAL_TRACKS,
    **BALANCED_TRACKS,
    **CHARACTER_TRACKS,
}

__all__ = ["TRACKS", "get_track", "list_tracks", "random_track"]


def get_track(name: str) -> dict:
    """Return track dict by lowercase key. Raises KeyError if not found."""
    return TRACKS[name]


def list_tracks() -> list[str]:
    """Return sorted list of all track keys."""
    return sorted(TRACKS.keys())


def random_track() -> str:
    """Return a random track key."""
    return _random.choice(list(TRACKS.keys()))
