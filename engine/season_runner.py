"""Season runner — orchestrates a full championship season."""

import os

from .car_loader import load_all_cars
from .race_runner import run_race
from .season import get_season, create_custom_season
from .championship import create_standings, award_points, format_standings
from .car_development import create_dev_state, award_dev_points


def run_season(car_dir: str = "cars", season_name: str = "short",
               custom_tracks: list[str] | None = None,
               laps: int = 5, output_dir: str = "season_output") -> dict:
    """Run a full championship season and return results."""
    if custom_tracks:
        calendar = create_custom_season(custom_tracks, laps=laps)
    else:
        calendar = get_season(season_name)

    os.makedirs(output_dir, exist_ok=True)
    cars = load_all_cars(car_dir)
    standings = create_standings()
    dev_states = {car["CAR_NAME"]: create_dev_state(car) for car in cars}
    season_results = []

    print(f"\n{'=' * 60}")
    print(f"  {calendar['name']} — {len(calendar['races'])} rounds")
    print(f"{'=' * 60}")

    for race_info in calendar["races"]:
        round_num = race_info["round"]
        track = race_info["track"]
        race_laps = race_info.get("laps", laps)
        output = os.path.join(output_dir, f"round_{round_num}_{track}.json")

        print(f"\n{'─' * 40}")
        print(f"  Round {round_num}: {track.upper()}")
        print(f"{'─' * 40}")

        results = run_race(
            car_dir=car_dir, track_name=track, laps=race_laps,
            output=output, race_number=round_num,
        )

        award_points(standings, results)
        for r in results:
            name = r["name"]
            if name in dev_states:
                award_dev_points(dev_states[name], r.get("position", 99))

        season_results.append({
            "round": round_num, "track": track, "results": results,
        })

        print(f"\n{format_standings(standings)}")

    print(f"\n{'=' * 60}")
    print(f"  FINAL {calendar['name'].upper()} STANDINGS")
    print(f"{'=' * 60}")
    print(format_standings(standings))

    return {
        "calendar": calendar,
        "standings": standings,
        "dev_states": dev_states,
        "races": season_results,
    }
