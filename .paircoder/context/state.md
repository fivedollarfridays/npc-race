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
Wave 1 (parallel): T46.1 (ghost levels), T46.4 (efficiency HUD)         [7 Cx]
Wave 2:            T46.2 (ghost race runner)                             [3 Cx]
Wave 3 (parallel): T46.3 (ghost CLI), T46.5 (ghost in viewer)           [5 Cx]
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

- **T45.3 (trial CLI):** Added `npcrace trial` CLI command. Created `cli/trial_command.py` with `cmd_trial()` — resolves car dir (auto-detect or explicit), validates track, runs `run_time_trial()`, generates coaching tips, and prints formatted output. Extracted to separate module to stay within arch function-count limit on `commands.py`. 5 tests passing, ruff clean, arch check clean.
- **T45.2 (coaching tips):** Created `engine/coaching.py` with `generate_coaching()` and `format_trial_output()`. Generates actionable tips for gearbox (shift point), cooling (drag), fuel mix (lambda), and combined efficiency loss. Terminal output includes efficiency bars with annotations. 7 tests passing, ruff clean, arch check clean.
- **T45.4 (efficiency in frames):** Added `efficiency_product`, `gearbox_efficiency`, and `cooling_efficiency` to replay frame export. Stored individual efficiencies in car state via `run_efficiency_tick()`, passed through `_to_legacy_states()`, and included in `record_frame()`. 6 tests passing, 33 regression tests green.
- **T45.1 (trial engine):** Created `engine/time_trial.py` with `run_time_trial()` and `find_player_car()`. Runs a single-car 1-lap sim in ~0.38s wall time (Monza). Returns `TrialResult` with lap_time, sector_times, and per-part efficiency. 8 tests passing.

## What's Next

- T45.5 (edit loop verification) — Wave 4 (GATE)

## Pending
- Sprint 43 (security hardening) — planned, not started
- Sprint 44 (quality polish) — planned, not started
- Sprint 41 (grid + dashboard wiring) — planned, not started
