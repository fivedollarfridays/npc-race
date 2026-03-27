# Current State

> Last updated: 2026-03-26.

## Active Plan

**Plan:** Digital Training Wheels — Progressive Learning Game Loop
**Reference:** docs/proposal-training-wheels.md

## Sprint 45 — Time Trial + Coaching (14 Cx)

```
Wave 1 (parallel): T45.1 (trial engine) DONE, T45.4 (efficiency in frames) DONE  [6 Cx]
Wave 2:            T45.2 (coaching tips) DONE                            [3 Cx]
Wave 3:            T45.3 (trial CLI) DONE                                [3 Cx]
Wave 4 (GATE):     T45.5 (edit loop verification)                        [2 Cx]
```

## Sprint 46 — Ghost System + Viewer HUD (17 Cx)

```
Wave 1 (parallel): T46.1 (ghost levels) DONE, T46.4 (efficiency HUD) DONE [7 Cx]
Wave 2:            T46.2 (ghost race runner) DONE                        [3 Cx]
Wave 3 (parallel): T46.3 (ghost CLI) DONE, T46.5 (ghost in viewer) DONE [5 Cx]
Wave 4 (GATE):     T46.6 (ghost ladder playthrough)                      [2 Cx]
```

## Sprint 47 — Tiered Grid + Progression (11 Cx)

```
Wave 1:            T47.1 (tier system)                                   [3 Cx]
Wave 2:            T47.2 (tiered run command)                            [3 Cx]
Wave 3:            T47.3 (progression tracking)                          [3 Cx]
Wave 4 (GATE):     T47.4 (full progression playthrough)                  [2 Cx]
```

## What Was Just Done

- **T46.5 (ghost in viewer):** Added ghost rendering to viewer. In `car-renderer.js`: added `isGhostCar()` detection (by name "Ghost"/"Tortoise" or color "#555555") and translucent rendering via `globalAlpha = 0.5` with reset after draw. In `efficiency-panel.js`: added "You" / "Ghost" header labels, ghost comparison column (`eff-ghost-*` elements) with color-coded values (red if ghost worse, green if better), `ghost-delta` gap display, and `updateGhostDelta()` function. Updated `main.js` to pass `allCars` to `updateEfficiencyPanel()`. 9 tests passing, no regressions on existing 25 ghost/efficiency tests.
- **T46.3 (ghost CLI):** Created `cli/ghost_command.py` with `cmd_ghost()` -- resolves car dir (auto-detect or explicit), validates track and level (1-5), runs `run_ghost_race()`, prints `format_ghost_result()` output. Wired into `cli/main.py` with `_add_ghost_parser()` (--track, --level, --car-dir flags) and dispatch entry. 7 tests passing, ruff clean, arch check clean.
- **T46.2 (ghost race runner):** Created `engine/ghost_race.py` with `run_ghost_race()`, `GhostResult` dataclass, `format_ghost_result()`, and helpers `_run_sim()`, `_build_result()`, `_extract_efficiency()`, `_fmt_time()`. Runs player car vs ghost in a 2-car PartsRaceSim, returns side-by-side times, winner, margin, per-part efficiency comparison, ghost flaw info, and next_level progression. Level 1 default_project vs Ghost: player wins by ~1.7s on Monza. 7 tests passing, ruff clean, arch check clean.
- **T46.1 (ghost levels):** Created `engine/ghost.py` with `GHOST_LEVELS` dict (5 levels), `create_ghost()`, `_build_ghost()`, and `_load_rival()`. Levels 1-2 teach gearbox (shift RPM flaws), level 3 teaches cooling (overcooling drag), level 4 teaches strategy (never pits), level 5 loads Tortoise rival via `car_loader.load_car()`. 8 tests passing, ruff clean, arch check clean.
- **T46.4 (efficiency HUD):** Created `viewer/js/efficiency-panel.js` with `initEfficiencyPanel()` and `updateEfficiencyPanel()`. Added efficiency-panel div, CSS styles, and script tag to `dashboard.html`. Wired init calls into both WS and file-load paths in `main.js`, plus per-frame update next to `updateTelemetryPanel`. Color-coded bars: green >= 0.95, yellow 0.85-0.95, red < 0.85. 10 tests passing, ruff clean.
- **T45.3 (trial CLI):** Added `npcrace trial` CLI command. Created `cli/trial_command.py` with `cmd_trial()` — resolves car dir (auto-detect or explicit), validates track, runs `run_time_trial()`, generates coaching tips, and prints formatted output. Extracted to separate module to stay within arch function-count limit on `commands.py`. 5 tests passing, ruff clean, arch check clean.
- **T45.2 (coaching tips):** Created `engine/coaching.py` with `generate_coaching()` and `format_trial_output()`. Generates actionable tips for gearbox (shift point), cooling (drag), fuel mix (lambda), and combined efficiency loss. Terminal output includes efficiency bars with annotations. 7 tests passing, ruff clean, arch check clean.
- **T45.4 (efficiency in frames):** Added `efficiency_product`, `gearbox_efficiency`, and `cooling_efficiency` to replay frame export. Stored individual efficiencies in car state via `run_efficiency_tick()`, passed through `_to_legacy_states()`, and included in `record_frame()`. 6 tests passing, 33 regression tests green.
- **T45.1 (trial engine):** Created `engine/time_trial.py` with `run_time_trial()` and `find_player_car()`. Runs a single-car 1-lap sim in ~0.38s wall time (Monza). Returns `TrialResult` with lap_time, sector_times, and per-part efficiency. 8 tests passing.

## What's Next

- T46.6 (ghost ladder playthrough) — Wave 4 gate

## Pending
- Sprint 43 (security hardening) — planned, not started
- Sprint 44 (quality polish) — planned, not started
- Sprint 41 (grid + dashboard wiring) — planned, not started
