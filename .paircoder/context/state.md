# Current State

> Last updated: 2026-03-23. Sprint 33 merged to main. Planning Sprint 34-35.

## Active Plan

**Plan:** Full Race Distance, Qualifying, and Player UX
**Reference:** docs/proposal-full-race-distance.md (approved)

## Completed Phases

| Phase | Sprints | Status |
|-------|---------|--------|
| Phase 0: Baseline | S23 | ✅ |
| Phase 1: Core physics | S24-28 | ✅ |
| Phase 2: Code quality | S27 | ✅ |
| Phase 3: Car project loader | S29 | ✅ |
| Phase 4: League + Viewer | S30-31 | ✅ |
| Phase 5: Submission + Leaderboard | S32-33 | ✅ |

## Sprint 34 — Fast Sim + Qualifying (29 Cx)

**Goal:** 53-lap / 20-car Monza under 10 min. Qualifying grid.

### Wave 0: Pre-Sprint
- T34.0a: Wire webbrowser.open into cmd_run (1 Cx) -- DONE
- T34.0b: Fix reliability_score persistence (1 Cx) -- DONE

### Wave 1: Sparse Storage (sequential)
- T34.1: Lap summary accumulator (3 Cx) -- DONE
- T34.2: Fast mode in RaceSim (5 Cx) -- DONE
- T34.3: Fast mode results export + CLI (3 Cx) -- DONE

### Wave 2: Sim Performance (parallel, independent of Wave 1)
- T34.4: Strategy throttle 1Hz (3 Cx) -- DONE
- T34.5: Spatial neighbor lookup (3 Cx) -- DONE
- T34.6: Precompute track invariants (2 Cx) -- DONE

### Wave 3: Qualifying (sequential)
- T34.7: Qualifying simulation (5 Cx) -- DONE
- T34.8: Grid export + race pipeline (3 Cx) -- DONE

## Sprint 35 — Full Grid + Real Distances (21 Cx)

### Wave 1 (parallel)
- T35.1: Archetype template factory (3 Cx)
- T35.2: Track real-laps update (2 Cx)

### Wave 2 (parallel)
- T35.3: Frontrunner rivals — 3 cars (3 Cx) — depends T35.1
- T35.4: Midfield rivals — 4 cars (3 Cx) — depends T35.1
- T35.5: Backmarker rivals — 4 cars (3 Cx) — depends T35.1
- T35.6: Wildcard rivals — 3 cars (3 Cx) — depends T35.1

### Wave 3-4
- T35.7: 20-car integration test (2 Cx) — depends T35.2-T35.6
- T35.8: Race summary dashboard (2 Cx) — depends T35.7

## What Was Just Done

- **T34.8**: Grid export + race integration + CLI pipeline (INTEGRATION GATE). New `cli/race_commands.py` with `cmd_qualify` and `cmd_race`. Added `qualify` and `race` subparsers to `cli/main.py`. Added `_reorder_by_grid()` and `grid_file` parameter to `run_race()` in `engine/race_runner.py`. Extracted `_apply_grid_file()` and `_print_race_banner()` helpers to keep `run_race` under 50 lines. 11 new tests in `tests/test_race_pipeline.py` covering: cmd_qualify grid export, grid JSON sorting, qualifying output printing, run_race grid_file parameter, cmd_race with/without --qualify flag, grid position ordering (P1 at front with offset 0, last car at -30), and CLI parser wiring for qualify/race subcommands. Sprint 34 complete -- all 82 Sprint 34 tests pass.

## What's Next

- Sprint 35: Full Grid + Real Distances (T35.1 through T35.8)

## Key Metrics

- **~2,000 tests** | CI green | Zero tech debt
- **Monza 5-lap, 6 cars**: 35s wall time, 113 MB replay
- **Target**: Monza 53-lap, 20 cars under 10 min
