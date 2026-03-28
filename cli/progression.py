"""Player progression tracking."""

import json
import os

DEFAULT_PROGRESS_PATH = os.path.join(
    os.path.expanduser("~"), ".npcrace", "progress.json",
)


def _load_progress(prog_path: str | None = None) -> dict:
    """Load progress from file, or return defaults for a new player."""
    if prog_path is None:
        prog_path = DEFAULT_PROGRESS_PATH
    if os.path.isfile(prog_path):
        with open(prog_path) as f:
            return json.load(f)
    return {
        "ghost_completed": {},
        "tier": "rookie",
        "races_won": 0,
        "tracks_completed": [],
    }


def _save_progress(data: dict, prog_path: str | None = None) -> None:
    """Save progress data to file."""
    if prog_path is None:
        prog_path = DEFAULT_PROGRESS_PATH
    os.makedirs(os.path.dirname(prog_path), exist_ok=True)
    with open(prog_path, "w") as f:
        json.dump(data, f, indent=2)


def get_player_tier(prog_path: str | None = None) -> str:
    """Read current tier from progression file, defaulting to rookie."""
    return _load_progress(prog_path).get("tier", "rookie")


def record_ghost_completion(
    track: str, level: int, prog_path: str | None = None,
) -> dict:
    """Record beating a ghost level. Returns updated progress."""
    data = _load_progress(prog_path)
    ghosts = data.setdefault("ghost_completed", {})
    current = ghosts.get(track, 0)
    if level > current:
        ghosts[track] = level

    # Unlock midfield after beating Ghost Level 5 on any track
    if any(v >= 5 for v in ghosts.values()):
        if data["tier"] == "rookie":
            data["tier"] = "midfield"

    _save_progress(data, prog_path)
    return data


def record_race_win(
    tier: str, prog_path: str | None = None,
) -> dict:
    """Record winning a race. Upgrades tier if conditions met."""
    data = _load_progress(prog_path)
    data["races_won"] = data.get("races_won", 0) + 1

    # Tier upgrades: winning at current tier advances to next
    if tier == "midfield" and data["tier"] == "midfield":
        data["tier"] = "front"
    elif tier == "front" and data["tier"] == "front":
        data["tier"] = "full"

    _save_progress(data, prog_path)
    return data


def get_progress_summary(prog_path: str | None = None) -> str:
    """Human-readable progress summary."""
    data = _load_progress(prog_path)
    tier = data.get("tier", "rookie")
    ghosts = data.get("ghost_completed", {})
    wins = data.get("races_won", 0)

    ghost_str = (
        ", ".join(f"{t}: L{v}" for t, v in ghosts.items())
        if ghosts else "none"
    )

    return (
        f"Tier: {tier.upper()}\n"
        f"Ghost levels: {ghost_str}\n"
        f"Race wins: {wins}"
    )


def reset_progress(prog_path: str | None = None) -> None:
    """Reset all progression (for testing)."""
    if prog_path is None:
        prog_path = DEFAULT_PROGRESS_PATH
    if os.path.isfile(prog_path):
        os.remove(prog_path)


def cmd_progress(_args) -> int:
    """CLI handler: print progression summary."""
    print(get_progress_summary())
    return 0
