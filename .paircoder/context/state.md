# Current State

> Last updated: 2026-03-15 T1.4 done

## Active Plan

**Plan:** plan-2026-03-npc-race-v1 — NPC Race -- Ship v1.0
**Status:** Planned (11 tasks, 4 sprints)
**Current Sprint:** 1 (Wave 1: tracks + engine decomposition)

## Current Focus

T1.3 and T1.4 done. T1.5 (track integration) next, then T1.6.

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
| T1.7 | CLI packaging -- npcrace via pyproject.toml | pending | 45 | T1.5, T1.6 |
| T1.8 | viewer.html -- show track name in header | pending | 15 | T1.5 |

### Sprint 4 — Wave 4: Polish + Validation

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T1.9 | Balance testing -- all cars on all tracks | pending | 40 | T1.1, T1.5 |
| T1.10 | car_template.py -- final strategy state docs | pending | 15 | T1.9 |
| T1.11 | Integration tests -- end-to-end on named tracks | pending | 35 | T1.5, T1.6, T1.3, T1.4 |

**Total complexity: 400 | Estimated tokens: ~330k**

### Backlog

None.

## What Was Just Done

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

1. T1.3 and T1.4 (security) done. Sprint 2 security tasks complete.
2. T1.5 (integrate tracks into engine) ready -- depends on T1.1 + T1.2 (both done)
3. T1.6 (play.py --track flag) depends on T1.5
4. T1.11 (integration tests) now has T1.3 + T1.4 deps satisfied, still needs T1.5 + T1.6

## Blockers

None currently.

## Notes

- engine.py decomposed into engine/ package (T1.2), all files under 400 lines
- npc-wars bot_scanner.py and sandbox.py to be copied and adapted (T1.3, T1.4)
- Trello is not connected for this project (trello.enabled: false)
- No external dependencies allowed -- Python stdlib only
