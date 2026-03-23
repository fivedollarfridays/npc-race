"""Fast mode export utilities for NPC Race.

Writes lightweight lap_summary.json when running in fast mode
(skipping the full replay.json).
"""

import json


def export_lap_summary(sim, path: str) -> None:
    """Write lap_summary.json from RaceSim's accumulator."""
    summaries = sim.get_lap_summaries()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
