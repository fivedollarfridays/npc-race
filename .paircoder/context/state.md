# Current State

> Last updated: 2026-03-15 T1.10 done

## Active Plan

**Plan:** plan-2026-03-npc-race-v1 — NPC Race -- Ship v1.0
**Status:** Planned (11 tasks, 4 sprints)
**Current Sprint:** 1 (Wave 1: tracks + engine decomposition)

## Current Focus

T1.10 done. car_template.py updated with complete strategy docs and 3 example strategies.

## Task Status

### Sprint 1 — Wave 1: Foundation (parallel, no deps)

| ID | Task | Status | Complexity |
|----|------|--------|------------|
| T1.1 | tracks.py -- 20 named track presets | done | 60 |
| T1.2 | Decompose engine.py into modules (<400 lines) | done | 50 |

### Sprint 2 — Wave 2: Security + Integration (depends on Wave 1)

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T1.3 | Security -- bot_scanner.py for car files | done | 40 | T1.2 |
| T1.4 | Security -- sandbox.py for car execution | done | 40 | T1.2 |
| T1.5 | Engine -- integrate tracks.py + track selection | pending | 35 | T1.1, T1.2 |
| T1.6 | play.py -- add --track and --list-tracks | pending | 25 | T1.5 |

### Sprint 3 — Wave 3: CLI + Viewer

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T1.7 | CLI packaging -- npcrace via pyproject.toml | done | 45 | T1.5, T1.6 |
| T1.8 | viewer.html -- show track name in header | pending | 15 | T1.5 |

### Sprint 4 — Wave 4: Polish + Validation

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T1.9 | Balance testing -- all cars on all tracks | done | 40 | T1.1, T1.5 |
| T1.10 | car_template.py -- final strategy state docs | done | 15 | T1.9 |
| T1.11 | Integration tests -- end-to-end on named tracks | done | 35 | T1.5, T1.6, T1.3, T1.4 |

**Total complexity: 400 | Estimated tokens: ~330k**

### Backlog

None.

## What Was Just Done

### Session: 2026-03-15 - T1.10 car_template.py final docs

- Updated `car_template.py` docstring (59 -> 135 lines, under 200 limit)
- Added complete strategy state field reference with exact types, ranges, and descriptions
  - All 13 fields documented: speed (float), position (int), total_cars (int), lap (int), total_laps (int), tire_wear (float 0-1), boost_available (bool), boost_active (bool), curvature (float), nearby_cars (list of dicts), distance (float), track_length (float), lateral (float -1 to 1)
  - nearby_cars sub-fields: name (str), distance_ahead (float), speed (float), lateral (float)
- Added complete return value docs with defaults and tire wear rates per mode
- Added 3 commented example strategy patterns: defensive (tire-saver), aggressive (full-send), draft-and-pass
- Created `tests/test_car_template.py` (104 lines) with 13 tests verifying imports, constants, budget, strategy returns, line count, docstring completeness, field types, example presence, and nearby_cars fields
- All 186 tests passing, ruff clean, file importable

### Session: 2026-03-15 - T1.9 Balance testing

- Created `tests/test_balance.py` (148 lines) with 7 tests across 3 test classes
- TestRaceCompletion (3): all cars finish all tracks, deterministic results, all 5 cars present
- TestNoDominance (2): no car wins >60% of tracks, at least 2 different winners
- TestTrackCharacterDiversity (2): power vs technical have different winners, no car sweeps both
- Created `scripts/balance_report.py` (132 lines) -- runs all 5 cars on 12 tracks, prints position matrix and win summary
- Tuned physics in `engine/simulation.py` `_apply_physics()`:
  - Replaced old curvature penalty formula with curvature-severity blend model
  - base_max_speed = 120 + power*160 - weight*50 (was 160 + power*100 - weight*25)
  - Corner speed uses linear blend: target = base_max*(1-severity) + grip_speed*severity
  - curv_severity = min(1.0, curv*47.0) -- controls power/grip tradeoff crossover
  - grip_speed = 50 + effective_grip*280 -- wider grip range for meaningful differentiation
  - mass_factor = 1.0 + weight*1.2 (was weight*0.5) -- heavier weight penalty
  - accel_rate = (40 + power*100) / mass_factor (was 60 + power*80)
- Balance results across 12 tracks: GooseLoose 6 wins (50%), Silky 5 wins (42%), GlassCanon 1 win (8%)
- No car exceeds 60% win rate -- balance threshold met
- Power tracks split between GooseLoose and Silky, technical tracks similarly split
- All 173 tests passing, ruff clean, files under limits

### Session: 2026-03-15 - T1.11 Integration tests

- Created `tests/test_integration.py` (213 lines) with 21 tests across 9 test classes
- TestNamedTrackRace (3): track_name in replay, all cars present, schema complete
- TestProceduralTrack (2): backward compat with seed-based tracks, default 3 laps
- TestAllSeedCarsFinish (2): all 5 seed cars finish 1-lap race, correct car count
- TestReplaySchema (3): track xy points, result fields, non-empty frames
- TestCarValidation (2): missing stats rejected, over-budget rejected
- TestMaliciousCarCaught (2): import os rejected, eval() call rejected
- TestTrackSelection (4): get_track valid, unknown raises, random_track, list_tracks 20
- TestCLI (2): --list-tracks output, --track monza produces correct replay
- TestEndToEnd (1): full pipeline -- create cars, validate, run race, verify replay
- All 21 integration tests passing, 169 total tests passing, ruff clean
- File is 213 lines, well under 600-line test file limit

### Session: 2026-03-15 - T1.7 CLI packaging

- Created `cli/` package with hub-and-spoke pattern: `__init__.py` (8 lines), `main.py` (67 lines), `commands.py` (92 lines)
- 5 subcommands: `run`, `init`, `validate`, `list-tracks`, `wizard` (stub)
- `npcrace run` mirrors play.py behavior (--car-dir, --laps, --seed, --track, --output) without auto-browser
- `npcrace init` creates cars/ dir and copies car_template.py
- `npcrace validate` runs bot_scanner on positional car file args
- `npcrace list-tracks` prints all 20 tracks with country and character
- `npcrace wizard` prints "not yet implemented" stub
- Created `pyproject.toml` with `[project.scripts] npcrace = "cli.main:main"` entry point
- play.py continues to work as standalone script
- 16 tests in `tests/test_cli.py` (213 lines) across 6 test classes
- 145 total tests passing, ruff clean, all files under limits

### Session: 2026-03-15 - T1.3 bot_scanner for car files

- Created `security/bot_scanner.py` (268 lines) with ALLOWLIST import model
- ALLOWED_IMPORTS: math, random, collections, itertools, functools -- anything else rejected
- BLOCKED_CALLS: eval, exec, compile, __import__, open, getattr, setattr, delattr, globals, locals, vars, type, dir
- BLOCKED_DUNDER_ATTRS: __globals__, __builtins__, __subclasses__, __mro__, __bases__, __class__, __code__, __closure__
- Module-level code: only imports, assignments, definitions, docstrings, pass, `if __name__` guard
- Semicolons blocked inside strategy() function body
- Car metadata validation: CAR_NAME non-empty string, CAR_COLOR valid hex, 5 stats present/numeric/>=0, budget <= 100
- `scan_car_source(source)` and `scan_car_file(path)` return ScanResult dataclass
- 36 tests in `tests/test_bot_scanner.py` (519 lines) across 9 test classes
- All 5 seed cars pass scanning
- 129 total tests passing, ruff clean

### Session: 2026-03-15 - T1.4 sandbox.py for car execution

- Created `security/sandbox.py` (95 lines) with `safe_strategy_call()` wrapper
- Deep copies state before passing to strategy (protects caller from mutation)
- Exception handling: catches all errors, returns defaults
- Timeout enforcement via daemon thread with configurable `timeout_ms` (default 100ms)
- Return type validation: non-dict returns trigger defaults
- Partial merge: missing keys filled from defaults dict
- Throttle validation: clamped to 0.0-1.0, non-numeric falls back to default
- Tire mode validation: must be "conserve", "balanced", or "push"
- Default decisions: `{"throttle": 1.0, "boost": False, "tire_mode": "balanced"}`
- Updated `security/__init__.py` to use try/except imports (safe for parallel T1.3)
- 23 tests in `tests/test_sandbox.py` (183 lines) across 6 test classes
- All 129 tests passing, ruff clean

### Session: 2026-03-15 - T1.2 engine decomposition

- Decomposed monolithic `engine.py` (495 lines) into `engine/` package with hub-and-spoke pattern
- Created 5 files: `__init__.py` (24 lines, hub), `track_gen.py` (88 lines), `car_loader.py` (79 lines), `simulation.py` (322 lines), `race_runner.py` (51 lines)
- All modules well under 400-line limit (largest: simulation.py at 322 lines)
- Refactored RaceSim.step() into smaller helper methods (_step_car, _apply_boost, _apply_tire_wear, _apply_physics, _apply_drafting, _update_distance, _record_frame) to keep functions under 50 lines
- Hub re-exports full public API: RaceSim, run_race, generate_track, interpolate_track, compute_track_data, load_car, load_all_cars, STAT_BUDGET, STAT_FIELDS, REQUIRED_FIELDS
- `from engine import run_race` backward compat preserved -- play.py works unmodified
- Old engine.py moved to `_engine_legacy.py` (backup)
- 28 tests in `tests/test_engine_modules.py` (295 lines) across 6 test classes: TestTrackGen (5), TestCarLoader (6), TestSimulation (5), TestRaceRunner (3), TestHubReExports (7), TestFileSizes (2)
- All tests passing, ruff clean, no circular imports
- Verified play.py runs a full 1-lap race with 5 cars successfully

### Session: 2026-03-15 - T1.1 tracks.py

- Created `tracks/` package with hub-and-spoke architecture: `__init__.py` (hub, 37 lines), `power.py` (108 lines), `technical.py` (80 lines), `balanced.py` (128 lines), `character.py` (197 lines)
- 20 named track presets with control points approximating real-world circuits scaled to 800x700 canvas
- Power (4): Monza, Baku, Jeddah, Spa
- Technical (3): Monaco, Singapore, Zandvoort
- Balanced (5): Silverstone, Suzuka, Austin, Barcelona, Bahrain
- Character (8): Interlagos, Imola, Melbourne, Montreal, Mugello, Lusail, Hungaroring, Shanghai
- Helper functions: `get_track(name)`, `list_tracks()`, `random_track()`
- 21 tests in `tests/test_tracks.py` (165 lines) covering track count, required fields, control point bounds, character distribution, expected names, helper functions, and key-name consistency
- All tests passing, ruff clean, arch clean

### Session: 2026-03-15 - Plan Creation

- Read project spec at docs/npc-race-spec.md
- Created plan `plan-2026-03-npc-race-v1` (feature, 11 tasks, 4 sprints)
- Wrote detailed task files with acceptance criteria, dependencies, and implementation plans
- Organized into 4 waves with dependency ordering:
  - Wave 1: tracks.py + engine decomposition (parallel)
  - Wave 2: security + engine integration + play.py updates
  - Wave 3: CLI packaging + viewer updates
  - Wave 4: balance testing + template updates + integration tests
- Noted engine.py is 495 lines (over 400 limit, must decompose in T1.2)

## What's Next

1. T1.10 (car_template.py docs) done.
2. T1.8 (viewer.html track name) pending -- depends on T1.5
3. T1.5 (engine track integration) pending -- blocks T1.6, T1.8

## Blockers

None currently.

## Notes

- engine.py decomposed into engine/ package (T1.2), all files under 400 lines
- npc-wars bot_scanner.py and sandbox.py to be copied and adapted (T1.3, T1.4)
- Trello is not connected for this project (trello.enabled: false)
- No external dependencies allowed -- Python stdlib only
