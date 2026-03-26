"""CLI command for solo time trial."""

import os

from tracks import TRACKS


def cmd_trial(args) -> int:
    """Run a solo time trial with coaching output."""
    from engine.time_trial import find_player_car

    # Resolve car directory
    car_dir = args.car_dir
    if car_dir is None:
        car_dir = find_player_car()
        if car_dir is None:
            print("Error: No player car found. Run 'npcrace init my_car' first.")
            return 1

    if not os.path.isdir(car_dir):
        print(f"Error: Car directory not found: {car_dir}")
        return 1

    # Validate track
    track = args.track.lower()
    if track not in TRACKS:
        print(f"Unknown track: '{args.track}'")
        print(f"Available: {', '.join(sorted(TRACKS))}")
        return 1

    # Run trial
    from engine.coaching import format_trial_output, generate_coaching
    from engine.time_trial import run_time_trial

    result = run_time_trial(car_dir, track)
    tips = generate_coaching(result)
    print(format_trial_output(result, tips))
    return 0
