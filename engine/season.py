"""Season calendar — curated track sequences for championship mode."""

from tracks import list_tracks

PRESET_SEASONS = {
    "short": [
        {"round": 1, "track": "bahrain", "laps": 5},
        {"round": 2, "track": "monza", "laps": 5},
        {"round": 3, "track": "silverstone", "laps": 5},
        {"round": 4, "track": "monaco", "laps": 5},
        {"round": 5, "track": "spa", "laps": 5},
    ],
    "full": [
        {"round": i + 1, "track": t, "laps": 5}
        for i, t in enumerate([
            "bahrain", "monza", "silverstone", "monaco", "spa",
            "singapore", "interlagos", "hungaroring", "baku", "suzuka",
        ])
    ],
    "classic": [
        {"round": i + 1, "track": t, "laps": 5}
        for i, t in enumerate([
            "monza", "spa", "silverstone", "suzuka",
            "interlagos", "monaco", "bahrain", "singapore",
        ])
    ],
}


def get_season(name: str) -> dict:
    """Return a preset season calendar by name."""
    races = PRESET_SEASONS.get(name)
    if races is None:
        raise ValueError(f"Unknown season: {name}. Available: {list_seasons()}")
    return {"name": f"{name.title()} Championship", "races": list(races)}


def create_custom_season(tracks: list[str], laps: int = 5, name: str = "Custom") -> dict:
    """Create a custom season from a track list."""
    available = set(list_tracks())
    for t in tracks:
        if t not in available:
            raise ValueError(f"Unknown track: {t}")
    races = [{"round": i + 1, "track": t, "laps": laps} for i, t in enumerate(tracks)]
    return {"name": f"{name} Championship", "races": races}


def list_seasons() -> list[str]:
    """Return available preset season names."""
    return sorted(PRESET_SEASONS.keys())
