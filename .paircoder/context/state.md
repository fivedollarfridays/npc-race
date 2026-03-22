# Current State

> Last updated: 2026-03-22 Phase 1 closed. Sprints 24-28 complete.

## Active Plan

**Plan:** NPC Race v3 — Build a Car Out of Code (Master Plan)
**Reference:** docs/proposal-npc-race-v3.md (updated with final numbers)

## Phase 1: CLOSED ✓

Physics foundation stable. 6/9 parts with positive sensitivity through honest physics. No artificial hacks.

| Metric | 1-Lap | 5-Lap |
|--------|-------|-------|
| Baseline | 81.13s | 393.77s |
| Optimized | 75.33s | 376.00s |
| Spread | 5.80s | 17.77s |
| Parts > 0.3s | 6/9 | 2/4 multi-lap |

## Phase 2: Code Quality — DONE ✓ (Sprint 27)

AST metrics, reliability score (0.50-1.00), glitch engine with reliability_scale knob. Wired into race loop.

## Next: Phase 3 — Multi-file Car Project Loader

## Future
- Phase 4: League system + live code terminal + TRON viewer
- Phase 5: Infrastructure (submission pipeline, onboarding)

## What Was Just Done

- **T29.5**: Integration gate for car project loader. Created `tests/test_car_project_integration.py` with 10 end-to-end tests covering: project car completes race, mixed cars race together, partial project defaults fill (3 loaded + 7 defaults), source enables reliability scoring, malicious helper caught by scanner, and all 5 seed cars still load and race. All 10 tests passing. Ruff clean, arch check clean.

- **T29.3 done** (auto-updated by hook)

- **T29.3**: Wired car project loader into race runner. Updated `engine/car_loader.py` so `load_all_cars()` detects both single-file cars and directory-based car projects (subdirs with `car.py`). Added `_source` population for all cars. Projects are security-scanned via `scan_car_project()` before loading; malicious projects are skipped with warning. Refactored `load_car()` by extracting `_apply_components`, `_extract_parts`, `_extract_hardware_specs` to fix function length violation. 6 new tests in `tests/test_car_loader_projects.py`, all 20 car loader tests passing. 6 cars now load from `cars/` (5 single-file + 1 default_project).

- **T29.4**: Default car project template. Created `cars/default_project/` with car.py (metadata), engine_map.py, gearbox.py, strategy.py (3 F3 parts with teaching docstrings), and README.md (quick-start guide, 39 lines). All .py files under 30 lines. 15 tests in `tests/test_default_project.py`, all passing. Ruff clean.

- **T29.1**: Multi-file car project loader. Created `engine/car_project_loader.py` with `load_car_project()` that loads a directory as a car project: metadata from car.py, per-part .py files for custom part functions, defaults for missing parts, `_loaded_parts` tracking, `_source` concatenation, hardware specs with defaults. 9 tests in `tests/test_car_project_loader.py`, all passing. 88 lines implementation, 130 lines tests.

- **T29.2**: Deep import scanner for car projects. Added `scan_car_project()` that walks the full import graph of directory-based car projects, detecting forbidden imports buried in helpers, circular imports, missing modules, and relative imports. Extracted into `security/project_scanner.py` (hub-and-spoke) with re-export from `bot_scanner.py`. 8 new tests in `tests/test_bot_scanner_v3.py`, all 64 scanner tests passing.

- **Sprint 28**: Diff + suspension physics rewiring. Differential: speed-dependent optimal lock (traction peaks at 20% low speed, 70% high speed). Suspension: ride height drag + stronger ground effect (0.3→0.5). Both produce positive sensitivity. 6/9 parts above 0.3s, 0 negative.

- **Sprint 27**: Code quality system (Phase 2). AST metrics, reliability score, glitch engine. Removed suspension/differential from efficiency product.

- **Sprint 26**: Physics bug fixes. ERS lap reset, lateral G formula (50x fix), tire wear calibration.

- **Sprints 24-25**: Efficiency engine + physics-emergent rewiring.

## Completed Sprints

Sprints 1-9: Core game engine (tracks, viewer, realism, dashboard, drama)
Sprints 10-11: Weather, ERS, brakes
Sprints 17-23: Parts engine foundation
Sprints 24-28: Physics + code quality (Phase 1 + Phase 2)

## Key Metrics

- **Monza 1-lap**: 81.13s baseline, 75.33s optimized (5.80s spread)
- **Monza 5-lap**: 393.77s baseline, 376.00s optimized (17.77s spread)
- **6/9 parts above 0.3s**: gearbox, suspension, cooling, ERS deploy, fuel_mix, differential
- **Tire wear**: 12.5% after 5 laps
- **Lateral G**: 1.7-3.0G in corners (correct physics)

## Notes

- 3 parts at 0.00s 1-lap (engine_map, brake_bias, ers_harvest) — known multi-lap parts
- v3.1 proposal updated with final numbers (Sprint 28)
- Gate criteria: 1-lap 3-6s spread, 6+ parts >0.3s, no part >1.5s, no part >30%
