"""Race report generator — post-race summary from events and results."""

from .commentary import format_event, format_time


def generate_report(results, events, commentary, track_name="Unknown"):
    """Generate post-race text report."""
    winner = results[0] if results else {"name": "Unknown"}
    dotd_name, dotd_reason = find_driver_of_the_day(results)
    decisive = find_decisive_moment(events)
    sc_count = sum(1 for e in events if e.type == "SAFETY_CAR")
    spin_count = sum(1 for e in events if e.type == "SPIN")
    overtake_count = sum(1 for e in events if e.type == "OVERTAKE")

    lines = [
        f"{track_name.upper()} GP — RACE REPORT",
        f"Winner: {winner['name']}",
        f"Decisive moment: {decisive}" if decisive else "",
        f"Safety cars: {sc_count} | Spins: {spin_count} | Overtakes: {overtake_count}",
        f"Driver of the day: {dotd_name} ({dotd_reason})",
        "",
        "KEY MOMENTS:",
    ]
    # Top 10 events as key moments
    for i, event in enumerate(events[:10], 1):
        lines.append(f"  {i}. {format_event(event)}")
    if not events:
        lines.append("  (clean race — no major incidents)")
    return "\n".join(line for line in lines if line is not None)


def find_decisive_moment(events):
    """Find the most impactful event (latest P1 overtake or SC)."""
    impact = [e for e in events if e.type in ("OVERTAKE", "SAFETY_CAR")
              and (e.data.get("position") == 1 or e.type == "SAFETY_CAR")]
    if impact:
        latest = max(impact, key=lambda e: e.tick)
        return format_event(latest)
    if events:
        return format_event(events[-1])
    return "Clean race"


def find_driver_of_the_day(results):
    """Return (name, reason) for best performer.

    Simple heuristic: fastest lap holder, or winner if no lap data.
    """
    with_laps = [(r["name"], r.get("best_lap_s", 999)) for r in results
                  if r.get("finished") and r.get("best_lap_s")]
    if with_laps:
        best = min(with_laps, key=lambda x: x[1])
        return best[0], f"fastest lap {format_time(best[1])}"
    if results:
        return results[0]["name"], "race winner"
    return "Unknown", "no data"
