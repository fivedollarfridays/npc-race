"""Commentary generator — converts race events into broadcast-style text."""


def format_event(event) -> str:
    """Convert a RaceEvent into a commentary string."""
    t = event.type
    cars = event.cars
    d = event.data or {}
    if t == "OVERTAKE":
        return f"LAP {d.get('lap', '?')} — {cars[0]} passes {cars[1]} for P{d.get('position', '?')}!"
    if t == "BATTLE":
        return f"BATTLE — {cars[0]} vs {cars[1]}, gap {d.get('gap', 0):.1f}s"
    if t == "PIT_STOP":
        return f"PIT STOP — {cars[0]} boxes for {d.get('compound', 'tires')}"
    if t == "SAFETY_CAR":
        return f"SAFETY CAR DEPLOYED — {d.get('reason', 'incident')}"
    if t == "SPIN":
        return f"SPIN — {cars[0]} loses it!"
    if t == "DNF":
        return f"RETIREMENT — {cars[0]} out of the race"
    if t == "FASTEST_LAP":
        time_s = d.get("time", 0)
        return f"FASTEST LAP — {cars[0]} sets {format_time(time_s)}"
    return f"{t} — {', '.join(cars)}"


def format_events(events: list) -> list[str]:
    """Convert all events into commentary strings."""
    return [format_event(e) for e in events]


def format_time(seconds: float) -> str:
    """Format seconds as M:SS.mmm."""
    mins = int(seconds // 60)
    secs = seconds % 60
    return f"{mins}:{secs:06.3f}"
