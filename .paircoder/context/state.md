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
- T35.1: Archetype template factory (3 Cx) -- DONE
- T35.2: Track real-laps update (2 Cx) -- DONE

### Wave 2 (parallel)
- T35.3: Frontrunner rivals — 3 cars (3 Cx) — depends T35.1 -- DONE
- T35.4: Midfield rivals — 4 cars (3 Cx) — depends T35.1 -- DONE
- T35.5: Backmarker rivals — 4 cars (3 Cx) — depends T35.1 -- DONE
- T35.6: Wildcard rivals — 3 cars (3 Cx) — depends T35.1 -- DONE

### Wave 3-4
- T35.7: 20-car integration test (2 Cx) — depends T35.2-T35.6 -- DONE
- T35.8: Race summary dashboard (2 Cx) — depends T35.7 -- DONE

## What Was Just Done

- **T35.8**: Race summary dashboard (integration gate). Created `engine/race_dashboard.py` (200 lines) with 4 sections: standings table with gaps/pit counts/best laps, lap chart (every 5th lap), pit stop summary with compound transitions, and key moments (fastest lap + winning margin). Wired into `engine/race_runner.py` so dashboard prints after every race. Fast mode shows all 4 sections; live mode shows standings + key moments only. 11 tests in `tests/test_race_dashboard.py`. Gate verified: real 3-lap Monza race produces RACE RESULTS, LAP CHART, KEY MOMENTS output. Ruff clean, arch check clean.

## What's Next

- Sprint 35 complete. All tasks done.

## Key Metrics

- **~2,000 tests** | CI green | Zero tech debt
- **Monza 3-lap, 20 cars**: ~17s wall time
- **Monza 5-lap, 6 cars**: 35s wall time, 113 MB replay
- **Target**: Monza 53-lap, 20 cars under 10 min
