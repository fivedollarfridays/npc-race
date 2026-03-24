# Current State

> Last updated: 2026-03-23. Sprint 36 in progress.

## Active Plan

**Plan:** Test Tier Restructure (Sprint 36)
**Problem:** 2,310 tests, 462 run real sim, CI timing out at 10 min with real lap counts

## Completed

| Phase | Sprints | Status |
|-------|---------|--------|
| Core physics + quality | S23-28 | ✅ |
| Car projects + league | S29-31 | ✅ |
| Submission + leaderboard | S32-33 | ✅ |
| Fast sim + qualifying | S34 | ✅ |
| Full grid + real distances | S35 | ✅ |

## Sprint 36 — Test Tier Restructure (18 Cx)

**Goal:** CI on-push < 3 min. All sim tests use explicit laps.

```
Wave 1 (parallel):  T36.1 (pin laps), T36.3 (fixtures)         [8 Cx]
Wave 2 (sequential): T36.2 (marks) — depends T36.1              [3 Cx]
Wave 3 (parallel):  T36.4 (convert tests), T36.5 (CI workflow)  [5 Cx]
Wave 4 (GATE):      T36.6 (verify timing)                       [2 Cx]
```

- T36.1: Pin all sim tests to explicit laps (5 Cx) -- DONE
- T36.2: Apply pytest marks: unit/smoke/integration (3 Cx) -- DONE
- T36.3: Shared test fixtures for mock race data (3 Cx) -- DONE
- T36.4: Convert CLI/export/dashboard tests to fixtures (3 Cx) -- DONE
- T36.5: Update CI workflow for tiered execution (2 Cx) -- DONE
- T36.6: Verify CI timing targets (2 Cx) — GATE

## Key Metrics

- **2,310 tests** | **19 cars** | **20 tracks (real F1 laps)**
- **462 tests call sim** — 246 short, 69 medium, 147 long
- **CI target**: < 3 min on push, < 15 min integration

## What Was Just Done

- **T37.4**: Integration test -- full onboarding flow (GATE). Created `tests/test_onboarding_flow.py` with 4 smoke-marked tests: `test_init_creates_unique_car`, `test_full_onboarding_flow` (init -> run -> submit -> leaderboard end-to-end gate), `test_league_output_is_quiet`, `test_no_default_project_on_grid`. All 4 pass. Uses `zzz-test-flow*` car names (avoids `_` prefix which car_loader skips). Helpers extracted to stay under 50-line function limit. Arch check and ruff clean.

## What's Next

- T36.6 (verify CI timing -- GATE)
