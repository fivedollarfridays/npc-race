# Current State

> Last updated: 2026-03-24. Sprint 39 in progress.

## Active Plan

**Plan:** Code Circuit Browser Flow (Sprints 39-41)
**Reference:** docs/proposal-code-circuit-browser-flow.md

## Completed

| Phase | Sprints | Status |
|-------|---------|--------|
| Core physics + quality | S23-28 | ✅ |
| Car projects + league | S29-31 | ✅ |
| Submission + leaderboard | S32-33 | ✅ |
| Fast sim + qualifying | S34 | ✅ |
| Full grid + real distances | S35 | ✅ |
| Test tiers | S36 | ✅ |
| Onboarding bugfixes | S37 | ✅ |
| Audit bugfixes | S38 | ✅ |

## Sprint 39 — Server Bootstrap (18 Cx)

```
Wave 1: T39.1 (FastAPI app) ✅, T39.2 (SQLite DB) ✅      [6 Cx]
Wave 2: T39.3 (auth) ✅, T39.4 (health) ✅                 [4 Cx]
Wave 3: T39.5 (submit-car) ✅, T39.6 (cars+tracks) ✅      [8 Cx]
```

### What Was Just Done

- **T42.3 done**: Verified core feedback loop -- edit code, see lap time change. Created tests/test_feedback_loop.py with 3 smoke tests. Gearbox shift point: 12800rpm=80.400s vs 11000rpm=81.530s (diff 1.130s). Cooling effort: 1.0=82.430s vs 0.1=83.200s (diff 0.770s). Both PASS. Strategy engine_mode: push vs conserve = identical times (0.000s diff) -- KNOWN GAP: efficiency_engine calls strategy but never applies engine_mode to physics (xfail with strict=True). 2 passed, 1 xfail.

- **T42.2 done**: Swapped RaceSim -> PartsRaceSim in engine/race_runner.py. Changed import from .simulation to .parts_simulation, replaced RaceSim instantiation with PartsRaceSim. Updated 3 mock patches in tests/test_data_persistence.py (RaceSim -> PartsRaceSim). Added 6 new tests in tests/test_parts_sim_swap.py (import verification, integration with 2-3 cars, results fields, all-finish, results.json export). All tests pass including existing test_simulation_v2 and test_data_persistence. Player part functions now affect race results.

- **T42.1 done**: Added fast_mode, car_data_dir, race_number, drs_zones params to PartsRaceSim. Added timings system (create_timing + update_timing per tick), states property alias, LapAccumulator integration in fast_mode (1Hz frame recording), _detect_lap_completions, and get_lap_summaries. 15 new tests in test_parts_sim_compat.py, all passing. No regressions in existing test_parts_sim.py.

- **T39.6 done** (auto-updated by hook)

- **T39.6 done**: GET /api/cars + GET /api/tracks endpoints. Cars route lists player's cars (auth required) and gets car detail by ID (404 if not found). Tracks route returns all 20 tracks with metadata. 6 new tests passing, 33 total server tests green.
- **T39.5 done**: POST /api/submit-car endpoint (server/routes/submit.py). Validates empty source, runs bot_scanner security scan, extracts CAR_NAME/CAR_COLOR from AST, stores car in DB. Auto-creates player on first submit (returns api_key). 6 tests passing, 27 total server tests green.
- **T39.3 done** (auto-updated by hook)
- **T39.3 done**: API key auth dependency (server/auth.py). Auto-creates player + key on first request, validates existing keys, returns 401 on invalid. 3 tests passing, 21 total server tests green.
- **T39.4 done**: GET /api/health endpoint returning {"status": "ok", "version": "0.1.0"}. Created server/routes/ package with health router wired into app. 3 tests passing, 21 total server tests green.
- T39.1: FastAPI app skeleton with config, CORS middleware, and static/viewer mounts. 6 tests passing.
- T39.2: SQLite DB layer with players, api_keys, cars tables. All CRUD ops (create/get player, API keys, store/get cars). 9 tests passing.

### What's Next
- T42.4+ (remaining Sprint 42 tasks) or next sprint. Note: strategy engine_mode needs wiring in efficiency_engine.py (future task).

## Sprint 40 — Lobby + Landing + Editor (24 Cx)

```
Wave 1: T40.1 (lobby), T40.4 (landing page)               [8 Cx]
Wave 2: T40.2 (lobby routes), T40.3 (fill cars)            [6 Cx]
Wave 3: T40.5 (editor with Monaco)                         [5 Cx]
Wave 4: T40.6 (analysis panels)                            [5 Cx]
```

## Sprint 41 — Grid + Dashboard + Results (19 Cx)

```
Wave 1: T41.1 (race orchestrator)                          [5 Cx]
Wave 2: T41.2 (race API), T41.3 (grid), T41.4 (dashboard)  [9 Cx]
Wave 3: T41.5 (results overlay), T41.6 (localStorage)      [5 Cx]
```

## Key Metrics

- **~2,400 tests** | **20 cars** | **20 tracks** | CI green
- Game playable end-to-end via CLI
- Browser flow: landing → editor → lobby → race → results (3 sprints)
