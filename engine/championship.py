"""Championship points system — F1 points, standings, tiebreakers."""

F1_POINTS = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]


def create_standings() -> dict:
    """Return empty standings dict: {name: {"points": 0, "wins": 0, ...}}."""
    return {}


def award_points(standings: dict, results: list) -> dict:
    """Award F1 points from race results. Returns updated standings."""
    for r in results:
        name = r["name"]
        if name not in standings:
            standings[name] = {"points": 0, "wins": 0, "podiums": 0}
        pos = r.get("position", 99)
        if pos <= len(F1_POINTS):
            standings[name]["points"] += F1_POINTS[pos - 1]
        if pos == 1:
            standings[name]["wins"] += 1
        if pos <= 3:
            standings[name]["podiums"] += 1
    return standings


def get_sorted_standings(standings: dict) -> list[tuple[str, int]]:
    """Return standings sorted by points (desc), tiebroken by wins."""
    items = [(name, data["points"], data.get("wins", 0))
             for name, data in standings.items()]
    items.sort(key=lambda x: (-x[1], -x[2]))
    return [(name, pts) for name, pts, _ in items]


def format_standings(standings: dict) -> str:
    """Format standings as a printable table."""
    sorted_s = get_sorted_standings(standings)
    lines = ["CHAMPIONSHIP STANDINGS", "=" * 40]
    for i, (name, pts) in enumerate(sorted_s, 1):
        data = standings[name]
        lines.append(f"  P{i}  {name:12s}  {pts:3d} pts  ({data['wins']}W {data['podiums']}P)")
    return "\n".join(lines)
