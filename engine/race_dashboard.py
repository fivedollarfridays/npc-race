"""Race summary dashboard — rich terminal output for full-distance races."""

from __future__ import annotations


def _format_time_hms(total_s: float) -> str:
    """Format seconds as H:MM:SS.s or M:SS.s."""
    hours = int(total_s // 3600)
    remainder = total_s - hours * 3600
    mins = int(remainder // 60)
    secs = remainder - mins * 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:04.1f}"
    return f"{mins}:{secs:04.1f}"


def _format_lap_time(lap_s: float | None) -> str:
    """Format a single lap time as M:SS.s."""
    if lap_s is None:
        return "---"
    mins = int(lap_s // 60)
    secs = lap_s - mins * 60
    return f"{mins}:{secs:04.1f}"


def _format_standings(
    results: list[dict], laps: int, track_name: str,
) -> str:
    """Build the standings table section."""
    title = track_name.upper() if track_name else "UNKNOWN"
    lines = [
        f"   RACE RESULTS — {title} ({laps} laps)",
        "   " + "=" * 70,
    ]
    leader_time: float | None = None
    for r in results:
        pos = r["position"]
        name = r["name"]
        if not r.get("finished"):
            lines.append(f"    P{pos:<3d} {name:15s}  DNF")
            continue
        total = r.get("total_time_s") or 0.0
        time_str = _format_time_hms(total)
        best = r.get("best_lap_s")
        best_str = f"best {_format_lap_time(best)}" if best else ""
        stops = r.get("pit_stops", 0)
        stop_word = "stop" if stops == 1 else "stops"
        if pos == 1:
            leader_time = total
            gap_str = "\u2014"
        else:
            gap = total - (leader_time or total)
            if gap >= 60:
                gap_str = f"+{_format_time_hms(gap)}"
            else:
                gap_str = f"+{gap:.1f}s"
        league = r.get("league", "F3")
        lines.append(
            f"    P{pos:<3d} {name:15s}  {time_str:>12s}  "
            f"{gap_str:>10s}  {stops} {stop_word:5s}  {best_str:>10s}  {league}"
        )
    return "\n".join(lines)


def _lap_sample_indices(total_laps: int, step: int = 5) -> list[int]:
    """Return lap numbers to display in the chart (every Nth + final)."""
    indices = list(range(step, total_laps, step))
    if not indices or indices[-1] != total_laps:
        indices.append(total_laps)
    return indices


def _format_lap_chart(
    lap_summaries: dict[str, list[dict]], results: list[dict],
) -> str:
    """Build a compact lap chart showing position at sampled laps."""
    if not lap_summaries:
        return ""
    # Determine total laps from data
    max_laps = max(len(laps) for laps in lap_summaries.values())
    if max_laps == 0:
        return ""
    sample = _lap_sample_indices(max_laps)
    # Header row
    name_width = 15
    header_parts = [f"   {'Car':<{name_width}s}"]
    for lap_num in sample:
        header_parts.append(f"L{lap_num:<4d}")
    header_parts.append("FIN")
    header = "  ".join(header_parts)

    lines = ["   LAP CHART (every 5th lap)", header]

    # Sort by finishing position
    order = [r["name"] for r in sorted(results, key=lambda r: r["position"])]
    for name in order:
        car_laps = lap_summaries.get(name, [])
        row_parts = [f"   {name:<{name_width}s}"]
        for lap_num in sample:
            idx = lap_num - 1
            if idx < len(car_laps):
                pos = car_laps[idx].get("position", "?")
                row_parts.append(f"{pos:<5d}" if isinstance(pos, int) else f"{pos:<5s}")
            else:
                row_parts.append("  -  ")
        # Final position from results
        for r in results:
            if r["name"] == name:
                row_parts.append(str(r["position"]))
                break
        lines.append("  ".join(row_parts))
    return "\n".join(lines)


def _format_pit_stops(lap_summaries: dict[str, list[dict]]) -> str:
    """Build the pit stop summary section from lap summaries."""
    if not lap_summaries:
        return ""
    lines = ["   PIT STOPS"]
    any_pits = False
    for car_name, laps_data in lap_summaries.items():
        stops = []
        prev_compound = None
        for entry in laps_data:
            compound = entry.get("tire_compound", "unknown")
            if entry.get("pit_stop"):
                transition = f"{prev_compound}->{compound}" if prev_compound else compound
                stops.append(f"L{entry['lap']} {transition}")
            prev_compound = compound
        if stops:
            any_pits = True
            lines.append(f"   {car_name:15s}  {'  '.join(stops)}")
    if not any_pits:
        return ""
    return "\n".join(lines)


def _format_key_moments(results: list[dict]) -> str:
    """Build the key moments section from race results."""
    moments: list[str] = []
    # Fastest lap
    best_car = None
    best_time: float | None = None
    best_lap_num: int | None = None
    for r in results:
        bl = r.get("best_lap_s")
        if bl is not None and (best_time is None or bl < best_time):
            best_time = bl
            best_car = r["name"]
            lap_times = r.get("lap_times", [])
            if lap_times:
                best_lap_num = lap_times.index(min(lap_times)) + 1
            else:
                best_lap_num = None
    if best_car and best_time is not None:
        lap_ref = f" on L{best_lap_num}" if best_lap_num else ""
        moments.append(
            f"FASTEST LAP -- {best_car} {_format_lap_time(best_time)}{lap_ref}"
        )
    # Winner margin
    if len(results) >= 2:
        p1 = results[0]
        p2 = results[1]
        t1 = p1.get("total_time_s") or 0
        t2 = p2.get("total_time_s") or 0
        gap = t2 - t1
        if gap > 0:
            moments.append(
                f"WINNING MARGIN -- {p1['name']} beats {p2['name']} by {gap:.1f}s"
            )
    if not moments:
        return ""
    lines = ["   KEY MOMENTS"]
    for i, m in enumerate(moments, 1):
        lines.append(f"   {i}. {m}")
    return "\n".join(lines)


def generate_dashboard(
    results: list[dict],
    lap_summaries: dict[str, list[dict]] | None = None,
    track_name: str = "",
    laps: int = 0,
) -> str:
    """Generate terminal race summary dashboard.

    Returns a single string with all dashboard sections.
    """
    sections = [_format_standings(results, laps, track_name)]
    if lap_summaries:
        chart = _format_lap_chart(lap_summaries, results)
        if chart:
            sections.append(chart)
        pits = _format_pit_stops(lap_summaries)
        if pits:
            sections.append(pits)
    moments = _format_key_moments(results)
    if moments:
        sections.append(moments)
    return "\n\n".join(sections)
