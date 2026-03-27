"""Ghost race CLI command."""

import os


def cmd_ghost(args) -> int:
    """Run a ghost race at the specified level."""
    from engine.ghost_race import format_ghost_result, run_ghost_race
    from engine.time_trial import find_player_car
    from tracks import TRACKS

    # Find car
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
        from tracks import list_tracks

        print(f"Available: {', '.join(sorted(list_tracks()))}")
        return 1

    # Validate level
    level = args.level
    if level < 1 or level > 5:
        print(f"Error: Level must be 1-5, got {level}")
        return 1

    # Run ghost race
    try:
        result = run_ghost_race(car_dir, track, level)
    except Exception as e:
        print(f"Error: {e}")
        return 1

    # Print formatted output
    print(format_ghost_result(result))
    return 0
