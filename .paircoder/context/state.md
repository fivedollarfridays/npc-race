# Current State

> Last updated: 2026-03-22 Sprint 32 in progress. Submission pipeline integration gate done.

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

- **T32.5**: Integration gate for submission pipeline. Created `tests/test_submission_pipeline.py` with 9 end-to-end tests across 5 test classes: run produces results file + all required fields + small size (3 tests), integrity valid on fresh results + tamper breaks hash (2 tests), cmd_submit validates pipeline results + rejects tampered (2 tests), tournament produces per-race results with valid integrity (1 test), existing run_race behavior unchanged (1 test). All 9 tests passing. Ruff clean, arch check clean.

- **T32.4**: CLI submit command (`npcrace submit`). Added `cmd_submit()` to `cli/commands.py` (validates results.json via `verify_integrity()`, prints summary with track/laps/league/positions/hash) and `_print_submit_summary()` helper. Added `submit` subparser to `cli/main.py` with `results_file` positional arg. Handles missing file, invalid JSON, and tampered integrity gracefully (returns 1). 6 tests in `tests/test_submit_command.py`: CLI parser accepts submit, missing file error, invalid JSON error, valid results passes, tampered results rejected, summary output verified. All passing. Ruff clean. commands.py at 244 lines (under 400 limit).

- **T32.3**: CLI results export alongside replay. Modified `engine/race_runner.py` (235 lines): added `_compute_results_path()` to derive results filename from replay path (replay.json -> results.json, race_monza.json -> race_monza_results.json), added `_export_results()` to generate and save lightweight summary via `generate_results_summary()`, updated `_export_replay()` signature to accept `cars` and `league`, updated `_load_and_filter_cars()` to return effective_league. Results file is ADDITIONAL output alongside replay, not a replacement. Console prints "Results saved to {path}". 7 tests in `tests/test_results_export.py`: produces results file (default and custom names), valid JSON, required fields, car positions, integrity hash present, replay still exists. All passing. Ruff clean.

- **T32.2**: Integrity hash for results summary. Added `compute_integrity_hash()` and `verify_integrity()` to `engine/results.py`. Hash is SHA-256 over deterministic JSON serialization of results data, excluding `timestamp` and `integrity` fields. Wired into `generate_results_summary()` so every summary includes an `integrity` field. 5 new tests in `tests/test_results.py`: hash present, verifies on unmodified, fails on tamper, ignores timestamp changes, deterministic. 11 total results tests passing. Ruff clean, arch check clean.

- **T32.1**: Results summary format. Created `engine/results.py` (64 lines) with `generate_results_summary()` that extracts a lightweight JSON-serializable summary (~10KB) from a full replay (10MB+). Includes version, track, laps, league, ISO 8601 timestamp, and per-car entries (name, position, total_time_s, best_lap_s, lap_times, finished, reliability_score, league, loaded_parts). Helper `_match_car()` links replay results to car dicts by name. 6 tests in `tests/test_results.py`: required fields, car fields, size < 50KB, no frames key, ISO timestamp, real 1-lap race integration. All passing. Ruff clean, arch check clean.

- **T31.5**: Integration gate for viewer pipeline. Created `tests/test_viewer_pipeline.py` with 22 tests across 7 test classes: race produces call_logs in replay (3 tests), call logs sampled at 1Hz with 30-tick spacing (2 tests), call log entry structure with valid statuses (3 tests), reliability scores in range (3 tests), replay file size reasonable and call logs not dominant (2 tests), viewer JS/HTML files exist with expected functions and wiring (7 tests), backward compat for old replays without call_logs/reliability (2 tests). All 22 tests passing. Ruff clean, arch check clean.

- **T31.3 + T31.4**: Live code terminal and code grade card for the viewer. Created `viewer/js/code-terminal.js` (83 lines) with `initCodeTerminal()`, `updateCodeTerminal()`, and `renderCodeGrade()`. Terminal displays part function calls synced to replay tick with color-coded status (green ok, yellow clamped, red glitch/error). Grade card shows reliability as A/B/C/D letter with percentage bar. Updated `viewer/dashboard.html` with `#codeTerminal` div, CSS for `.term-call`, `.term-badge`, `.grade-card`, `.grade-letter`, `.grade-fill` classes, and script tag. Wired into `viewer/js/main.js` (`initCodeTerminal` in `loadReplay`, `updateCodeTerminal` in `render`). 17 tests in `tests/test_viewer_code_terminal.py`, all 126 viewer tests passing. Ruff clean.

- **T31.2**: Export call logs to replay JSON format. Modified `engine/parts_simulation.py`: tagged log entries with `car_name` in `step()`, added `_build_sampled_call_logs()` method that samples at 1Hz (every 30th tick) and groups by car, added `reliability` dict to replay output. Per-car format: `{tick, parts: [{name, output, status, efficiency?}]}`. Efficiency omitted when 1.0 to save space. Call logs add ~1.6MB for a 5-lap race. 10 tests in `tests/test_call_log_export.py`, all passing. Ruff clean.

- **T31.1**: Audited and fixed proposal-npc-race-v3.md. Fixed: F3 parts (engine_map -> cooling), F2 parts (brakes -> fuel_mix), F3/F2 progression text, Championship target (~78-80s -> ~75-78s), "10-second spread" -> "5.80s spread", Phase statuses (1-3 DONE, 4 split into 4a DONE + 4b Future), success criteria item 7 marked done. Sections 3.3, 3.4, 12, 13 numbers were already correct from Sprint 28.

- **T30.4**: Integration gate for the league system. Created `tests/test_league_integration.py` with 8 end-to-end tests across 5 test classes: auto-detection (default_project -> F1 due to engine_map, seed cars all get league, single-file cars -> F3), F3 validation (valid parts pass, advisory report always passes), F2 detection (6-part car), enforced gates (high-CC code rejected at F1), and race integration (mixed-league cars complete 1-lap Monza race). 40 total league tests passing across 3 test files. Ruff clean.

- **T30.3**: League system wired into race runner and CLI. Added `_apply_league_gates()` to `engine/race_runner.py` that auto-detects league from car parts (highest tier wins) or validates against a specified league, generates quality reports, prints league status with advisory/rejection messages, and filters out cars that fail enforced gates (F1+). Added `--league` flag to CLI (`choices=["F3", "F2", "F1", "Championship"]`, default None). Refactored `run_race()` by extracting `_export_replay()`, `_load_and_filter_cars()` to stay under 50-line function limit; refactored `_build_parser()` by extracting `_add_run_parser()`, `_add_season_parser()`. 13 new tests in `tests/test_league_wiring.py` (230 lines), all passing. 32 total league tests passing. Ruff clean, arch check clean (warnings only).

- **T30.2**: Quality gate enforcement. Added `QualityReport` dataclass and `generate_quality_report()` to `engine/league_system.py` (166 lines). Advisory gates (F3/F2) always pass but include informational messages about CC and reliability. Enforced gates (F1) reject cars with CC > 15. Championship additionally requires reliability >= 0.88. Cars without `_source` default to passing. Uses AST metrics from `code_quality.py` (no subprocess ruff). 8 new tests in `TestQualityGates` class, 19 total in `tests/test_league_system.py` (211 lines). All passing, ruff clean.

- **T30.1**: League definitions and validation. Created `engine/league_system.py` (71 lines) with `LEAGUE_TIERS`, `LEAGUE_PARTS` dicts, `LeagueResult` dataclass, `determine_league()` (infers tier from loaded parts), and `validate_car_for_league()` (checks part restrictions). F3=3 parts, F2=6, F1=all 10, Championship=all 10 + project dir. 11 tests in `tests/test_league_system.py` (88 lines), all passing. Ruff clean.

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
