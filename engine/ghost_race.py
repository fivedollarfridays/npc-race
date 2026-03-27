"""Ghost race -- player car vs adversarial ghost."""

from __future__ import annotations

from dataclasses import dataclass

from engine import safe_call
from engine.car_project_loader import load_car_project
from engine.ghost import create_ghost, GHOST_LEVELS
from engine.parts_simulation import PartsRaceSim
from engine.track_gen import interpolate_track
from tracks import get_track


@dataclass
class GhostResult:
    """Side-by-side result of a player-vs-ghost race."""

    player_time: float
    ghost_time: float
    winner: str  # "player" or "ghost"
    margin: float  # seconds
    player_efficiency: dict[str, float]
    ghost_efficiency: dict[str, float]
    ghost_flaw: str
    ghost_description: str
    level: int
    next_level: int | None


def run_ghost_race(
    car_dir: str, track_name: str, level: int
) -> GhostResult:
    """Run player car vs ghost at given level."""
    config = GHOST_LEVELS[level]
    player = load_car_project(car_dir)
    ghost = create_ghost(level)

    sim = _run_sim(player, ghost, track_name, config)
    return _build_result(sim, player["CAR_NAME"], config, level)


def _run_sim(
    player: dict, ghost: dict, track_name: str, config: dict
) -> PartsRaceSim:
    """Run the 2-car simulation and return the sim object."""
    laps = config.get("laps", 1)
    td = get_track(track_name)
    pts = interpolate_track(td["control_points"], resolution=500)

    old_timeout = safe_call.TIMEOUT_ENABLED
    safe_call.TIMEOUT_ENABLED = False
    try:
        sim = PartsRaceSim(
            cars=[player, ghost],
            track_points=pts,
            laps=laps,
            seed=42,
            track_name=track_name,
            real_length_m=td.get("real_length_m"),
            fast_mode=True,
        )
        sim.run()
    finally:
        safe_call.TIMEOUT_ENABLED = old_timeout
    return sim


def _build_result(
    sim: PartsRaceSim, player_name: str, config: dict, level: int
) -> GhostResult:
    """Extract times, efficiencies, and winner from completed sim."""
    results = sim.get_results()
    player_r = next(r for r in results if r["name"] == player_name)
    ghost_r = next(r for r in results if r["name"] != player_name)

    p_time = player_r["total_time_s"]
    g_time = ghost_r["total_time_s"]

    return GhostResult(
        player_time=p_time,
        ghost_time=g_time,
        winner="player" if p_time <= g_time else "ghost",
        margin=abs(p_time - g_time),
        player_efficiency=_extract_efficiency(sim.call_logs, player_name),
        ghost_efficiency=_extract_efficiency(
            sim.call_logs, ghost_r["name"]
        ),
        ghost_flaw=config.get("flaw") or "none",
        ghost_description=config.get("description", ""),
        level=level,
        next_level=level + 1 if level < 5 else None,
    )


def _extract_efficiency(
    call_logs: list, car_name: str
) -> dict[str, float]:
    """Average per-part efficiency from call logs."""
    part_sums: dict[str, list[float]] = {}
    for tick_log in call_logs:
        for entry in tick_log:
            if entry.get("car_name") == car_name:
                part = entry.get("part", "")
                eff = entry.get("efficiency", 1.0)
                if part:
                    part_sums.setdefault(part, []).append(eff)
    return {p: sum(v) / len(v) for p, v in part_sums.items() if v}


def format_ghost_result(result: GhostResult) -> str:
    """Format ghost race result as terminal output."""
    laps = GHOST_LEVELS[result.level].get("laps", 1)
    lap_word = "lap" if laps == 1 else "laps"

    lines = [
        f"GHOST RACE -- Level {result.level} ({laps} {lap_word})",
        "",
    ]

    p_time = _fmt_time(result.player_time)
    g_time = _fmt_time(result.ghost_time)

    p_gb = result.player_efficiency.get("gearbox", 1.0)
    p_cool = result.player_efficiency.get("cooling", 1.0)
    g_gb = result.ghost_efficiency.get("gearbox", 1.0)
    g_cool = result.ghost_efficiency.get("cooling", 1.0)

    lines.append(
        f"  Your Car:    {p_time}  (gearbox: {p_gb:.2f}, cooling: {p_cool:.2f})"
    )
    lines.append(
        f"  Ghost:       {g_time}  (gearbox: {g_gb:.2f}, cooling: {g_cool:.2f})"
    )
    lines.append("")

    if result.winner == "player":
        lines.append(f"  You won by {result.margin:.1f} seconds!")
    else:
        lines.append(f"  Ghost won by {result.margin:.1f} seconds.")

    lines.append(f"  Ghost flaw: {result.ghost_description}")

    if result.next_level:
        next_desc = GHOST_LEVELS[result.next_level].get("description", "")
        lines.append("")
        lines.append(f"  NEXT: Level {result.next_level} -- {next_desc}")
    else:
        lines.append("")
        lines.append("  You beat all ghost levels! Ready for the grid.")

    return "\n".join(lines)


def _fmt_time(seconds: float) -> str:
    """Format seconds as m:ss.sss."""
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m}:{s:06.3f}"
