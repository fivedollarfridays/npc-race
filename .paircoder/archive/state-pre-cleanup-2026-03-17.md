# Current State

> Last updated: 2026-03-17 T3.10 balance testing + integration gate

## Active Plan

**Plan:** plan-2026-03-npc-race-viewer — Realistic Racing Viewer Upgrade
**Type:** feature
**Status:** Planned (11 tasks, 5 waves)
**Total Complexity:** 405 Cx

## Current Focus

T3.10 (integration gate) complete. Sprint 3 realism overhaul done. All 772 tests passing.

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
| T1.5 | Engine -- integrate tracks.py + track selection | done | 35 | T1.1, T1.2 |
| T1.6 | play.py -- add --track and --list-tracks | done | 25 | T1.5 |

### Sprint 3 — Wave 3: CLI + Viewer

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T1.7 | CLI packaging -- npcrace via pyproject.toml | done | 45 | T1.5, T1.6 |
| T1.8 | viewer.html -- show track name in header | done | 15 | T1.5 |

### Sprint 4 — Wave 4: Polish + Validation

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T1.9 | Balance testing -- all cars on all tracks | done | 40 | T1.1, T1.5 |
| T1.10 | car_template.py -- final strategy state docs | done | 15 | T1.9 |
| T1.11 | Integration tests -- end-to-end on named tracks | done | 35 | T1.5, T1.6, T1.3, T1.4 |

**Total complexity: 400 | Estimated tokens: ~330k**

### Sprint 2 — Realistic Racing Viewer Upgrade

#### Wave 1: Data Foundation (parallel)

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T2.1 | Enrich replay.json (curvatures, headings, seg) | done | 30 | — |
| T2.2 | Build system -- viewer JS inliner | done | 25 | — |
| T2.11 | Tests for T2.1 + T2.2 | pending | 25 | T2.1, T2.2 |

#### Wave 2: Canvas Infrastructure

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T2.3 | Layered canvas + data enrichment | done | 35 | T2.1, T2.2 |

#### Wave 3: Core Renderers (parallel)

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T2.4 | Track renderer | done | 45 | T2.3 |
| T2.5 | Car renderer | done | 45 | T2.3 |
| T2.6 | Broadcast overlay | done | 45 | T2.3 |
| T2.7 | Sound engine | done | 50 | T2.3 |

#### Wave 4: Effects + Camera (parallel)

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T2.8 | Physics visualization | done | 35 | T2.4, T2.5 |
| T2.9 | Camera system | done | 40 | T2.3, T2.6 |

#### Wave 5: Integration Gate

| ID | Task | Status | Complexity | Depends |
|----|------|--------|------------|---------|
| T2.10 | Integration + polish | done | 30 | all |

**Total complexity: 405 Cx**

## What Was Just Done

- **T3.10 done** -- Balance testing + integration gate for realism overhaul

### Session: 2026-03-17 - T3.10 Balance testing + integration gate

- Fixed world_scale: changed from `track_length / real_length_m` to calibrated `track_length / 3333.0`
  - Old formula produced inconsistent lap times (67s Monaco vs 111s Monza) because sim physics can't replicate real speed variance (160 vs 260 km/h avg)
  - New formula gives consistent 65-93s laps across all tracks
- Tuned physics constants for competitive balance:
  - `base_max_speed`: `155 + power * 90 * power_mode - weight * 60` (was `120 + power * 160 - weight * 50`)
  - `accel_rate`: `(50 + power * 60) / mass_factor * dt` (was `(40 + power * 100)`)
  - `grip_speed`: `60 + effective_grip * 300` (was `50 + effective_grip * 280`)
  - Engine modes: push power_mult 1.03 (was 1.05), conserve power_mult 0.95 (was 0.92), push consumption 1.25 (was 1.20)
  - Hard tire: base_grip 0.85 (was 0.88), wear_rate 0.00015 (was 0.00012), cliff 0.80 (was 0.85), exponent 2.5 (was 2.0)
- Balance result: Silky 3 wins, GlassCanon 3 wins (50/50 split across 6 tracks)
- Refactored `engine/race_runner.py`: extracted `_resolve_track()` and `_print_results()` to keep `run_race()` under 50 lines
- Created `tests/test_balance_v2.py` (148 lines, 12 tests across 5 classes):
  - TestAllCarsFinish: all 5 finish 5-lap Monaco
  - TestNoDominance: no car >60%, at least 2 different winners
  - TestLapTimes: Monaco 60-90s, Monza 65-95s
  - TestPitStopsAndFuel: at least 1 car pits, fuel decreases
  - TestReplayV2Fields: tire_compound, fuel_pct, engine_mode, pit_status, lateral present
- Created `scripts/balance_report_v2.py` (87 lines): runs all 5 cars on 6 tracks, prints wins/lap times
- Updated existing tests for new constant values:
  - test_fuel_model.py: push/conserve mode values
  - test_simulation_v2.py: world_scale tests (calibrated, not dependent on real_length_m)
  - test_tire_model.py: hard compound base_grip
- All 772 tests passing, ruff clean, arch check clean (simulation.py 335 lines/14 functions, warning only)
- Pit stops confirmed working: BrickHouse 2-stop, GooseLoose/Silky/SlipStream 1-stop, GlassCanon 0-stop
- Fuel confirmed decreasing: 1.0 -> 0.96-0.98 after 5 laps

- **T3.8 done** (auto-updated by hook)

- **T3.8 done** -- Rewrote all 5 seed car strategies for pit stops, fuel, lateral, engine modes

### Session: 2026-03-17 - T3.8 Seed car strategy rewrite

- Rewrote all 5 seed cars with distinct pit/fuel/lateral/engine strategies:
  - GooseLoose: 1-stop medium->hard, push engine first stint, lateral blocking when car behind is close
  - Silky: 1-stop soft->medium at ~35%, conserve engine, inside line in corners (lateral_target=-1.0)
  - GlassCanon: 0-stop on hards, push engine always, lateral blocking on straights, full throttle
  - BrickHouse: 2-stop soft->medium->hard at ~30%/~65%, push early/conserve late, wide lateral stance
  - SlipStream: 1-stop medium->soft at ~55% (late undercut), follows car ahead laterally, push on fresh softs
- All 5 cars return all new fields: lateral_target, pit_request, tire_compound_request, engine_mode
- Stats unchanged (all sum to 100, same as before)
- Created `tests/test_seed_cars_v2.py` (163 lines, 52 tests across 7 classes):
  - TestCarImportsAndBasics (15): all 5 import, have attrs, pass bot_scanner
  - TestStrategyReturns (15): all return throttle, lateral_target, engine_mode
  - TestPitStopStrategies (7): GooseLoose pits at 45%, GlassCanon never pits, BrickHouse pits twice, Silky at 35%, SlipStream at 55%
  - TestEngineModes (6): GooseLoose push/standard, Silky conserve, GlassCanon always push, BrickHouse push/conserve, SlipStream push on fresh softs
  - TestLateralBehaviors (4): GooseLoose blocks, Silky inside line, GlassCanon blocks on straights, SlipStream follows draft
  - TestFileSize (5): all files under 100 lines
- Extracted `_draft_info()` helper in slipstream.py to keep strategy function under 50 lines
- All 52 tests passing, ruff clean, arch check clean
- All car files under 100 lines (gooseloose: 55, silky: 53, glasscanon: 49, brickhouse: 59, slipstream: 61)

- **T3.9 done** -- Added new physics fields to replay per-car frame data

### Session: 2026-03-17 - T3.9 Replay v2 new physics fields

- Updated `engine/replay.py` (128 lines, 5 functions):
  - `record_frame()` now includes 5 new fields: tire_compound, fuel_pct, pit_status, engine_mode, lateral
  - All new fields use `.get()` with defaults for backward compatibility
  - fuel_pct computed as fuel_kg / max_fuel_kg, rounded to 2 decimals, division-safe
- Created `tests/test_replay_v2.py` (176 lines, 12 tests across 4 classes):
  - TestNewFrameFields (5): verifies all new fields present with correct values
  - TestFuelPctCalculation (4): full/empty/partial/zero-max-fuel edge cases
  - TestBackwardCompatibility (2): old state dicts without new fields don't crash, get defaults
  - TestExportReplayWithNewFields (1): export_replay passes through enriched frames
- All 80 related tests passing (replay + replay_v2 + simulation_v2 + integration), ruff clean
- replay.py at 128 lines (under 200 limit)

- **T3.7 done** -- Updated sandbox defaults/validation for new strategy fields + car_template docs

### Session: 2026-03-17 - T3.7 Sandbox v2 defaults + car_template docs

- Updated `security/sandbox.py` (140 lines, 10 functions):
  - DEFAULTS expanded: added lateral_target (0.0), pit_request (False), tire_compound_request (None), engine_mode ("standard")
  - Added VALID_ENGINE_MODES {"push", "standard", "conserve"} and VALID_COMPOUNDS {"soft", "medium", "hard"}
  - `_validate_lateral_target()`: clamps to [-1.0, 1.0], invalid/non-numeric defaults to 0.0
  - `_validate_engine_mode()`: validates against VALID_ENGINE_MODES, defaults to "standard"
  - `_validate_tire_compound_request()`: validates against VALID_COMPOUNDS, None passthrough, invalid defaults to None
  - `_merge_with_defaults()`: handles all 4 new fields (lateral_target, pit_request, engine_mode, tire_compound_request)
- Updated `car_template.py` (177 lines):
  - Documented 10 new strategy state fields: fuel_remaining, fuel_pct, tire_compound, tire_age_laps, engine_mode, pit_status, pit_stops, gap_ahead_s, gap_behind_s
  - Documented 4 new return fields: lateral_target, pit_request, tire_compound_request, engine_mode
  - Replaced Example 3 (draft-and-pass) with pit stop strategy example
  - Added Example 4 (draft-and-pass with lateral movement)
- Updated `tests/test_sandbox.py`: updated DEFAULTS reference to include new fields
- Created `tests/test_sandbox_v2.py` (166 lines, 24 tests across 5 classes):
  - TestNewFieldDefaults (5): old strategies get correct defaults for all new fields
  - TestLateralTargetValidation (5): clamp +2.0->1.0, -3.0->-1.0, "invalid"->0.0, valid accepted, None->0.0
  - TestEngineModeValidation (4): invalid->standard, push/conserve accepted, non-string->standard
  - TestTireCompoundRequestValidation (6): soft/medium/hard accepted, invalid->None, non-string->None, None->None
  - TestPitRequestValidation (4): True works, defaults False, truthy/falsy coercion
- All 114 key tests passing (sandbox + car_template + simulation_v2 + integration), ruff clean
- Backward compatible: old strategies returning only throttle/boost/tire_mode still work

- **T3.6 done** -- Wired all new physics systems into simulation loop

### Session: 2026-03-17 - T3.6 Simulation physics integration

- Modified `engine/simulation.py` (332 lines, 14 functions):
  - Added imports for tire_model, fuel_model, pit_lane functions
  - `__init__`: accepts `real_length_m`, computes `world_scale = track_length / real_length_m`
  - Per-car state: added tire_compound, tire_age_laps, fuel_kg, max_fuel_kg, fuel_base_rate, pit_state, engine_mode
  - `build_strategy_state`: added fuel_remaining, fuel_pct, tire_compound, tire_age_laps, engine_mode, pit_status, pit_stops, gap_ahead_s, gap_behind_s
  - `_step_car`: extracts engine_mode, pit_request, tire_compound_request from strategy; pit state machine (request -> update -> complete_pit_stop); inline fuel consumption
  - `_apply_tire_wear`: now uses compound-based wear via compute_wear(); tire_mode maps to throttle factor (push=1.0, balanced=0.7, conserve=0.4)
  - `_apply_physics`: compound grip via compute_grip_multiplier; engine mode power mult; pit speed limit; fuel weight via compute_weight_from_fuel
  - `_update_distance`: world_scale + 1/3.6 km/h->m/s conversion; pit_stationary blocks movement; tire_age_laps increments on lap change
  - `run()`: max_ticks default increased from 10000 to 36000 to account for km/h->m/s conversion
- Modified `engine/race_runner.py`: passes real_length_m from track_data to RaceSim
- Modified `engine/__init__.py`: exports get_compound, compute_grip_multiplier, get_compound_names, get_engine_mode, get_engine_mode_names, create_pit_state, is_in_pit
- Created `tests/test_simulation_v2.py` (378 lines, 33 tests across 12 classes):
  - TestWorldScale (5), TestCarStateFields (5), TestStrategyStateFields (6), TestFuelConsumption (2), TestTireCompoundIntegration (2), TestEngineMode (2), TestPitStopWiring (1), TestDistanceWithWorldScale (3), TestBackwardCompat (3), TestRaceRunnerIntegration (1), TestNewExports (3)
- All 665 tests passing (excluding balance tests which need retuning due to physics overhaul)
- Ruff clean, arch check clean (warning only: 332 lines)
- Known: balance tests (test_balance.py, 4 tests) fail because physics overhaul changed speed/distance relationship; requires separate balance retuning task
- Backward compatible: old strategies returning only throttle/boost/tire_mode still work

- **T3.4 done** (auto-updated by hook)

- **T3.4 done** -- Lateral movement system implemented in simulation.py

### Session: 2026-03-17 - T3.4 Lateral movement system

- Added `_apply_lateral(self, state, lateral_target, dt)` method to RaceSim in `engine/simulation.py`
  - Lerps car lateral position toward target at rate modulated by speed and grip
  - Speed reduces agility: faster cars are less agile (speed_factor = 1.0 - speed/300 * 0.6, min 0.2)
  - Grip from tire_model.compute_grip_multiplier affects lateral control
  - Proximity resistance: cars within 10 distance units and 0.3 lateral distance push apart
  - lateral_target clamped to [-1, 1], output lateral clamped to [-1, 1]
- Wired into `_step_car()`: extracts `lateral_target` from strategy decision (defaults to 0.0)
- Added `from . import tire_model` import to simulation.py
- simulation.py: 303 lines (under 400), 14 functions (under 15)
- Created `tests/test_lateral.py` (200 lines, 10 tests across 6 classes)
  - TestLateralMovesTowardTarget (3): positive/negative target, reaches near target over time
  - TestDefaultLateralTarget (1): no lateral_target stays near zero
  - TestSpeedReducesAgility (1): slow car moves laterally faster than fast car
  - TestLateralClamping (2): never exceeds 1.0 or goes below -1.0
  - TestProximityResistance (1): close cars at same lateral get pushed apart
  - TestBackwardCompatibility (2): old strategy without lateral_target works, empty dict works
- All 604 tests passing, ruff clean, arch check clean (warning only: 303 lines)
- Backward compatible: strategies without lateral_target default to 0.0

- **T3.1 done** -- Added real-world track data (real_length_m, real_laps) to all 20 tracks

### Session: 2026-03-17 - T3.1 Real-world track data (real_length_m, real_laps)

- Added `real_length_m` (int, meters) and `real_laps` (int, F1 race lap count) to all 20 track dicts
  - Power (4): Monza 5793m/53, Baku 6003m/51, Jeddah 6174m/50, Spa 7004m/44
  - Technical (3): Monaco 3337m/78, Singapore 5063m/62, Zandvoort 4259m/72
  - Balanced (5): Silverstone 5891m/52, Suzuka 5807m/53, Austin 5513m/56, Barcelona 4675m/66, Bahrain 5412m/57
  - Character (8): Interlagos 4309m/71, Imola 4909m/63, Melbourne 5278m/58, Montreal 4361m/70, Mugello 5245m/59, Lusail 5380m/57, Hungaroring 4381m/70, Shanghai 5451m/56
- Created `tests/test_time_calibration.py` (56 lines, 12 tests across 2 classes)
  - TestAllTracksHaveRealData (4): every track has both fields, both are positive integers
  - TestSpotCheckValues (8): spot-checks Monaco, Monza, Spa, Interlagos length and laps
- All 594 tests passing, ruff clean, all files under 400 lines
- No engine files modified -- only tracks/*.py

- **T3.2 done** -- Created engine/tire_model.py with three tire compounds
- **T3.5 done** -- Created engine/pit_lane.py with pit stop state machine
- **T3.3 done** (auto-updated by hook)

### Session: 2026-03-17 - T3.5 Pit lane state machine

- Created `engine/pit_lane.py` (89 lines, 6 functions) -- purely functional pit stop state machine
  - Constants: PIT_SPEED_LIMIT (80.0 km/h), PIT_ENTRY_TICKS (60), PIT_STOP_TICKS (660), PIT_EXIT_TICKS (60)
  - `create_pit_state()`: returns fresh pit state dict with 5 fields (status, pit_timer, pit_stops, requested_compound, pending_request)
  - `request_pit_stop(pit_state, compound_name)`: queues pit stop only when racing, sets pending_request and requested_compound
  - `update_pit_state(pit_state)`: ticks state machine: racing->pit_entry->pit_stationary->pit_exit->racing, returns (state, completed)
  - `is_in_pit(pit_state)`: returns True when status != "racing"
  - `get_speed_limit(pit_state)`: returns PIT_SPEED_LIMIT during pit_entry/pit_exit, None otherwise
  - `complete_pit_stop(pit_state)`: increments pit_stops, clears requested_compound, returns (state, compound_name)
- Created `tests/test_pit_lane.py` (266 lines, 35 tests across 7 classes)
  - TestCreatePitState (6): all default values correct
  - TestRequestPitStop (6): queues when racing, rejects during all pit phases, no mutation
  - TestUpdatePitStateTransitions (6): all 4 state transitions + timer decrement + no-op racing
  - TestUpdatePitStateDurations (4): entry/stationary/exit tick counts + full cycle
  - TestIsInPit (4): correct for all 4 statuses
  - TestGetSpeedLimit (4): limit during entry/exit, None for racing/stationary
  - TestCompletePitStop (5): increments counter, returns compound, clears state, no mutation
- Purely functional -- no state mutation, no external dependencies
- All 639 tests passing, ruff clean, files well under limits (89 < 200, 266 < 400)

### Session: 2026-03-17 - T3.2 Tire model module

- Created `engine/tire_model.py` (83 lines, 5 functions) -- three tire compounds with non-linear wear/grip curves
  - `COMPOUNDS` dict: soft (base_grip 1.15, wear 0.00040, cliff 0.75), medium (1.00, 0.00020, 0.80), hard (0.88, 0.00012, 0.85)
  - `get_compound(name)`: returns compound dict, defaults to medium for invalid names
  - `compute_wear(current_wear, compound_name, throttle, curvature)`: wear rate scales with throttle and curvature, capped at 1.0
  - `compute_grip_multiplier(wear, compound_name)`: linear degradation pre-cliff, exponential drop post-cliff with floor at 0.3
  - `is_past_cliff(wear, compound_name)`: boolean check against cliff_threshold
  - `get_compound_names()`: returns list of valid compound names
- Created `tests/test_tire_model.py` (223 lines, 28 tests across 6 classes)
- Purely functional -- no state mutation, no external dependencies
- All 28 tests passing, ruff clean, files well under limits

- **T3.3 done** -- Created engine/fuel_model.py with fuel consumption, engine modes, and weight computation

### Session: 2026-03-17 - T3.3 Fuel model module

- Created `engine/fuel_model.py` (72 lines, 5 functions) -- purely functional fuel load physics
  - Constants: BASE_CONSUMPTION_KG_PER_M (0.000055), FUEL_MARGIN (1.05), MAX_FUEL_WEIGHT_FACTOR (0.6)
  - ENGINE_MODES dict: push (1.20x consumption, 1.05x power), standard (1.00/1.00), conserve (0.80/0.92)
  - `get_engine_mode(name)`: returns mode dict, defaults to "standard" for invalid/None
  - `get_engine_mode_names()`: returns list of valid mode names
  - `compute_starting_fuel(laps, track_length_m)`: laps * length * base_rate * margin
  - `compute_fuel_consumption(throttle, engine_mode_name, base_rate_per_tick, dt)`: auto-calibrating per-tick consumption, throttle and mode modulate base rate
  - `compute_weight_from_fuel(fuel_kg, max_fuel_kg)`: normalized weight penalty 0-MAX_FUEL_WEIGHT_FACTOR, clamps negatives to 0
- Created `tests/test_fuel_model.py` (207 lines, 30 tests across 7 classes)
  - TestGetEngineMode (5): standard/push/conserve lookup, invalid defaults, None defaults
  - TestGetEngineModeNames (3): returns list, contains all modes, length matches
  - TestComputeStartingFuel (5): proportional to laps/length, Monza 53-lap sanity, margin included, zero laps
  - TestComputeFuelConsumption (7): zero throttle=0, push>standard>conserve, half throttle, dt scaling, never negative, invalid mode
  - TestComputeWeightFromFuel (6): full tank, empty tank, half tank, decreasing, range 0-1, negative clamp
  - TestConstants (4): positive base rate, margin>1, weight factor range, 3 engine modes
- All 30 tests passing, ruff clean, arch check clean
- No modifications to simulation.py or any existing files

- **T2.10 done** -- Integration gate complete

### Session: 2026-03-17 - T2.10 Integration + polish (INTEGRATION GATE)

- Removed old sidebar from `viewer/viewer.html`:
  - Deleted `<div class="sidebar">` with leaderboard and controls HTML
  - Removed all sidebar-only CSS: `.sidebar`, `.sidebar-title`, `.leaderboard`, `.car-row`, `.car-pos`, `.car-dot`, `.car-details`, `.car-name`, `.car-stats`, `.tire-bar`, `.tire-fill`, `.boost-indicator`, `.controls`, `.lap-display`
  - Track container now takes full width
- Added bottom control bar (`<div class="bottom-bar">`) inside track-container:
  - Row 1: Play button, speed buttons (0.5x/1x/2x/4x), scrubber range input
  - Row 2: Camera mode buttons (Track/Follow/Onboard), mute button, volume slider
  - CSS: position absolute, bottom 0, rgba background, z-index 20
- Cleaned up `viewer/js/main.js` (359 lines, down from 394):
  - Removed `updateLeaderboard()` function (24 lines) -- replaced by canvas overlay
  - Removed `updateLeaderboard(cars)` call from `renderOverlay()`
  - Removed `lapDisplay` element reference (lap info now in canvas overlay)
  - Kept `showResults()` for HTML finish overlay modal
- Verified all 8 INJECT markers in correct dependency order
- Verified backward compatibility: data-enrichment.js guards all computed fields, car-renderer.js handles missing seg
- Built viewer.html (58,423 bytes), all features integrated
- Created `tests/test_viewer_integration_gate.py` (215 lines, 39 tests across 8 classes)
- All 524 tests passing, zero regressions

- **T2.9 done** (auto-updated by hook)

### Session: 2026-03-17 - T2.9 Camera system (3 modes + smooth transitions)

- Created `viewer/js/camera.js` (136 lines, 9 functions) -- three camera modes with smooth lerp transitions
  - `cameraSystem` state object: mode, targetX/Y/Zoom/Rotation, currentX/Y/Zoom/Rotation, selectedCar, lerpSpeed (0.08)
  - `setCameraMode(mode)`: switches between 'full', 'follow', 'onboard'; auto-selects leader if no car selected
  - `selectCar(name)`: selects car for follow/onboard cam; auto-switches from full to follow mode
  - `updateCamera(replayData, frameIdx)`: dispatches to mode-specific update, then lerps current toward target
  - `_updateCameraFull()`: resets zoom to 1, rotation to 0 (default full-track view)
  - `_updateCameraFollow(cars, replayData)`: tracks selected car with look-ahead (30px in heading direction), zoom 3x
  - `_updateCameraOnboard(cars, replayData)`: tight zoom 6x, rotates so car faces up (-heading + PI/2), look-ahead 20px
  - `_getCarHeading(car, replayData)`: reads heading from track_headings array using car.seg index
  - `_lerpCamera()`: smooth interpolation of all 4 camera properties per frame
  - `updateCameraButtons()`: updates active class on .cam-btn elements
- Updated `viewer/js/main.js` (394 lines):
  - Removed old `camera` object, now uses `cameraSystem` from camera.js
  - `computeTransform()`: in non-full modes, uses cameraSystem.currentX/Y/Zoom for scale/offset; stores `_rotation`
  - `worldToScreen()`: applies rotation around canvas center using cos/sin transform when `_rotation !== 0`
  - `tick()`: calls `updateCamera(replay, frame)` before render; re-renders background in non-full modes
  - Keyboard shortcuts: T=full, F=follow, O=onboard, Escape=full (keydown listener)
  - Overlay click handler: clicking timing tower rows (x<200, y=60+row*30) calls `selectCar()`
- Updated `viewer/viewer.html`: INJECT marker for camera.js (after sound-engine, before main), 3 camera buttons (Track/Follow/Onboard) with cam-btn class
- Updated `tests/test_layered_canvas.py`: fixed test_has_camera_object to check both old camera and new cameraSystem
- Created `tests/test_camera_system.py` (123 lines, 22 tests) and `tests/test_camera_integration.py` (170 lines, 28 tests) -- 50 tests total across 9 classes
- Built viewer.html (61,666 bytes), all 485 tests passing, no regressions

- **T2.8 done** (physics visualization effects)

### Session: 2026-03-17 - T2.8 Physics visualization effects

- Created `viewer/js/physics-fx.js` (157 lines, 6 functions) -- physics-based visual effects
  - `physicsFx` state object: tireMarks array, maxMarks cap (2000)
  - `resetPhysicsFx()`: clears tire marks, called on replay load and scrub
  - `updateTireMarks(replay, frameIdx, transform)`: adds tire marks when curvature > 0.03 AND speed > 80, caps at maxMarks
  - `renderTireMarks(ctx, transform)`: draws dark circles (#111, radius 1.5*scale, alpha 0.15) on background canvas
  - `renderBrakeGlow(ctx, car, prevCar, screenX, screenY, heading, scale)`: radial gradient red glow (#ff0000) behind braking cars (speed drop > 5 km/h), intensity proportional to braking force
  - `renderDraftingWake(ctx, cars, replay, transform)`: faint translucent white lines (#ffffff10) between cars within 5-40 world units, 3 thin spread lines for slipstream visual
- Updated `viewer/viewer.html`: added `<!-- INJECT:js/physics-fx.js -->` between sound-engine.js and camera.js
- Updated `viewer/js/main.js` (394 lines):
  - `loadReplay()`: calls `resetPhysicsFx()` after enrichment
  - `renderBackground()`: calls `renderTireMarks()` after `renderTrack()`
  - `renderCars()`: calls `updateTireMarks()` at start, `renderBrakeGlow()` per car before renderCar, `renderDraftingWake()` after all cars
  - Scrubber handler: calls `resetPhysicsFx()` and `renderBackground()` on scrub
- Created `tests/test_physics_fx.py` (237 lines) with 33 tests across 8 classes
- Built viewer.html (61,666 bytes), all 485 tests passing, no regressions

- **T2.7 done** (auto-updated by hook)

### Session: 2026-03-17 - T2.7 Sound engine (Web Audio API procedural synthesis)

- Created `viewer/js/sound-engine.js` (208 lines, 9 functions) -- procedural audio via Web Audio API
  - `sound` object: AudioContext, master GainNode, engine/engine2 oscillators, aero/tire/crowd noise sources, muted/volume/initialized state
  - `initAudio()`: creates AudioContext and all audio nodes on first user interaction (autoplay policy gate)
  - Engine sound: two sawtooth oscillators (fundamental + 2nd harmonic), frequency scales 80-400 Hz with leader speed
  - Aero whoosh: white noise through lowpass filter (400 Hz), volume scales with speed
  - Tire squeal: white noise through bandpass filter (3000 Hz, Q=5), triggered by curvature * speed threshold
  - Crowd ambience: brown noise at low constant volume (0.05), with `triggerCrowdSwell()` for race events
  - `triggerDownshiftPop()`: short noise burst (50ms) on hard braking (speed drop > 20 km/h)
  - `pauseSound()`: fades all gain nodes to 0 via setTargetAtTime for artifact-free silence
  - `setVolume(vol)` / `toggleMute()`: master volume control with smooth transitions
  - `createNoiseBuffer()` / `createBrownNoiseBuffer()`: procedural noise generation, no external audio files
- Updated `viewer/viewer.html`: added INJECT marker for sound-engine.js, mute button and volume slider in controls
- Updated `viewer/js/main.js` (326 lines): wired initAudio on play, updateSound in tick, pauseSound on pause/scrub
- Created `tests/test_sound_engine.py` (192 lines) with 49 tests across 8 classes
- Built viewer.html (50,354 bytes), all 402 tests passing, no regressions

### Session: 2026-03-17 - T2.5 Top-down car model with wheels and effects

- Created viewer/js/car-renderer.js (271 lines) with renderCar(ctx, car, prevCar, replay, transform)
  - 9 drawing layers: shadow, boost glow, body, cockpit, rear wing, wheels, brake lights, position number, name label
  - Front wheels rotate by look-ahead steering angle; brake lights glow when speed drops >2 km/h
  - Boost effect: warm radial gradient behind exhaust area
- 12 helper functions for modular drawing
- Updated viewer/viewer.html with INJECT marker for car-renderer.js
- Refactored main.js renderCars(): delegates to renderCar() with prevCar for braking detection
- Created tests/test_car_renderer.py (217 lines, 29 tests across 6 classes)
- Built viewer.html (50,338 bytes), all 29 car renderer tests passing

### Session: 2026-03-17 - T2.6 F1-style broadcast overlay

- Created `viewer/js/overlay.js` (269 lines, 8 functions) -- canvas-based F1 TV-style broadcast overlay
  - `overlayState` object: overtakeQueue, lastPositions, lapTimes, fastestLap, lastLaps, lapStartFrames
  - `renderTimingTower(ctx, cars, replay, w, h)`: left-side panel with position numbers, 4px color bars, 3-char name abbreviations, speed in km/h, P1 gold accent, fastest-lap purple dot (#9900ff)
  - `renderLapCounter(ctx, replay, frame, w, h)`: top-center "LAP X / Y" badge with semi-transparent background, 600 16px Outfit font
  - `renderRaceStatus(ctx, replay, frame, w, h)`: status badge transitioning RACE (green #44cc44) -> FINAL LAP (yellow #ccaa00) -> CHEQUERED FLAG (gray)
  - `renderSpeedReadout(ctx, cars, w, h)`: leader speed in JetBrains Mono near lap counter
  - `renderOvertakeNotification(ctx, cars, prevCars, w, h, currentTime)`: detects position changes between frames, pushes "OVERTAKE -- {mover} passes {displaced} for P{pos}" to queue, renders with globalAlpha fade-out over 2s duration
  - `renderFastestLap(ctx, replay, frame, cars)`: tracks lap boundaries via lap field changes, records frame counts, updates fastestLap state
  - `renderBroadcastOverlay(ctx, replay, frame, w, h)`: main entry point calling all sub-renderers
  - `_roundRect(ctx, x, y, w, h, r)`: shared utility for rounded rectangle paths
- Updated `viewer/viewer.html` -- added `<!-- INJECT:js/overlay.js -->` between car-renderer.js and main.js
- Updated `viewer/js/main.js` -- renderOverlay() now clears overlay canvas and calls renderBroadcastOverlay() before HTML sidebar updates
  - main.js at 324 lines, well under 400 limit
- Created `tests/test_overlay.py` (177 lines) with 43 tests across 11 classes:
  - TestOverlayJsStructure (8): file exists, overlayState fields, entry point, param count
  - TestTimingTower (7): function exists, positions, color bars, abbreviations, speed/km/h, semi-transparent bg, P1 gold
  - TestLapCounter (3): function, LAP format, Outfit font
  - TestRaceStatus (6): function, RACE/FINAL LAP/CHEQUERED FLAG badges, green/yellow colors
  - TestSpeedReadout (1): function exists
  - TestOvertakeNotification (4): function, OVERTAKE text, globalAlpha fade, duration
  - TestFastestLap (2): function/state, purple #9900ff indicator
  - TestViewerHtmlOverlayInject (3): marker exists, after enrichment, before main
  - TestMainJsCallsOverlay (3): calls broadcast, clears canvas, passes dimensions
  - TestBuildWithOverlay (4): build succeeds, functions present, no markers, correct order
  - TestOverlayFileLimits (2): overlay.js < 400 lines, main.js < 400 lines
- Built viewer.html (50,273 bytes) via build_viewer.py
- 401 tests passing (1 pre-existing failure in test_sound_engine unrelated to T2.6)

### Session: 2026-03-17 - T2.4 Realistic track renderer

- Created `viewer/js/track-renderer.js` (255 lines) with `renderTrack(ctx, replay, transform)` function
  - 7 rendering layers drawn bottom-to-top: grass, run-off, asphalt, edge lines, kerbs, racing line, start/finish
  - Layer 1 (grass): dark green (#1a3a1a) fill with subtle darker patches for texture variation
  - Layer 2 (run-off): track path drawn with 2x track_width stroke in gravel gray (#3a3a3a)
  - Layer 3 (asphalt): track path in dark gray (#252530) with 4x4 noise texture pattern overlay via offscreen canvas + createPattern
  - Layer 4 (edge lines): white (#ffffff, lineWidth 1.5) lines computed from `replay._normals` on both sides
  - Layer 5 (kerbs): red (#cc0000) / white alternating blocks at points where `track_curvatures[i] > 0.04`, placed on inside of turn using cross product sign
  - Layer 6 (racing line): faint dashed line (#333340) with inside bias at corners using curvature-weighted normal offset
  - Layer 7 (start/finish): 2x6 checkered grid of alternating black/white squares at track[0], oriented using heading and normal
  - 8 helper functions (_drawGrass, _drawRunoff, _drawAsphalt, _drawEdgeLines, _drawKerbs, _drawRacingLine, _drawStartFinish, _drawTrackPath) keep each under 50 lines
- Updated `viewer/viewer.html` -- added `<!-- INJECT:js/track-renderer.js -->` between data-enrichment.js and main.js
- Updated `viewer/js/main.js` -- replaced 63-line inline renderBackground() with 7-line delegation to renderTrack()
  - main.js reduced from 394 to 339 lines
  - Passes `{ scale: _scale, ox: _ox, oy: _oy, w, h }` transform object
- Created `tests/test_track_renderer.py` (130 lines) with 23 tests across 5 classes:
  - TestTrackRendererFileExists (4): file exists, renderTrack function, correct params, under 300 lines
  - TestTrackRendererLayers (8): grass, run-off, asphalt, texture, edge lines, kerbs, racing line, start/finish
  - TestViewerShellInjectOrder (3): inject marker present, enrichment before renderer, renderer before main
  - TestMainJsCallsRenderTrack (3): calls renderTrack, passes transform, no old drawing code
  - TestBuildWithTrackRenderer (5): build succeeds, has renderTrack, 3 script blocks, correct order, no markers
- Built viewer.html at project root (27,395 bytes)
- All 286 tests passing (excluding pre-existing T2.5/T2.6 failures), no regressions

### Session: 2026-03-17 - T2.3 Layered canvas infrastructure + data enrichment

- Created `viewer/js/data-enrichment.js` (58 lines) -- client-side fallback for old replay files
  - `enrichReplayData(replay)` computes headings, curvatures, distances, normals when missing
  - Guards all fields with `if (!replay.field)` checks to preserve existing data
- Updated `viewer/viewer.html` -- replaced single `<canvas id="track">` with three stacked canvases:
  - `<canvas id="trackBg">` (background track surface)
  - `<canvas id="carLayer">` (car rendering)
  - `<canvas id="overlayLayer">` (HUD overlay)
  - CSS `.track-container canvas { position: absolute; top: 0; left: 0; }` for stacking
  - Added `<!-- INJECT:js/data-enrichment.js -->` before main.js inject marker
- Refactored `viewer/js/main.js` (394 lines, under 400 limit):
  - Three canvas refs: `bgCanvas`, `carCanvas`, `overlayCanvas` with separate 2D contexts
  - `worldToScreen(wx, wy)` transform function used by all renderers; supports camera modes
  - `computeTransform()` caches scale/offset for reuse
  - `renderBackground()` draws track surface on bgCanvas (called on load + resize only)
  - `renderCars()` draws cars on carCanvas (per frame)
  - `renderOverlay()` updates leaderboard/HUD (per frame)
  - `render()` calls only `renderCars()` + `renderOverlay()`
  - `camera` object exported: `{ x, y, zoom, rotation, mode: 'full' }`
  - `enrichReplayData(replay)` called in `loadReplay()` before rendering
- Created `tests/test_layered_canvas.py` (194 lines) with 34 tests across 4 classes:
  - TestDataEnrichmentJs (7): file exists, enrichReplayData function, headings/curvatures/distances/normals computation, guard checks
  - TestViewerShellThreeCanvases (8): three canvas IDs, no old canvas, CSS stacking, both INJECT markers, order
  - TestMainJsRefactored (11): worldToScreen, renderBackground/Cars/Overlay, render() calls subs, three canvas refs, camera, enrichReplayData call, under 400 lines
  - TestBuildWithLayeredCanvas (8): build succeeds, built output has enrich function, worldToScreen, three canvases, no markers, two scripts, correct order, playback controls
- Built viewer.html at project root (21,119 bytes) via `scripts/build_viewer.py`
- All 258 tests passing, no regressions

### Session: 2026-03-17 - T2.1 Enrich replay.json (curvatures, headings, seg)

- Added `compute_track_headings(track_points)` to `engine/track_gen.py` -- returns atan2-based heading angles per track point
- Added `"seg"` field to each car's frame dict in `engine/replay.py:record_frame()` (integer index into track array)
- Updated `engine/replay.py:export_replay()` to accept and include `track_curvatures` and `track_headings` arrays (rounded to 4 decimal places)
- Threaded curvatures and headings through `engine/simulation.py:RaceSim.export_replay()` to the export call
- Added 8 new tests to `tests/test_replay.py` (now 14 total): 3 for headings, 2 for seg, 3 for curvatures/headings in export
- All 224 tests passing, ruff clean, all files under limits

### Session: 2026-03-17 - T2.2 Build system -- viewer JS inliner

- Created `viewer/` directory with modular development structure:
  - `viewer/viewer.html` — HTML+CSS shell (310 lines) with `<!-- INJECT:js/main.js -->` marker
  - `viewer/js/main.js` — all JS extracted from original viewer.html (332 lines)
- Created `scripts/build_viewer.py` (47 lines) — inlines JS modules into single self-contained HTML
  - Reads shell, replaces INJECT markers with `<script>` wrapped file contents
  - Outputs to `viewer.html` at project root (16,982 bytes)
- Created `tests/test_build_viewer.py` (110 lines) with 21 tests across 3 classes:
  - TestViewerShell (6): shell exists, has INJECT marker, no inline script, doctype, styles, body
  - TestMainJs (4): JS file exists, contains togglePlay, replay state, render function
  - TestBuildScript (11): runs without error, output exists, has script tags, no INJECT markers, doctype, html end, NPC Race, replay.json, togglePlay, styles, size check
- All 224 tests passing, ruff clean, all files under arch limits

### Session: 2026-03-17 - T1.12 Integration gate (full test suite + arch check)

- Ran full pytest suite: 195 tests all passing (189 original + 6 new)
- Ruff lint: all clean, no violations
- Architecture check on all source files:
  - All files under 400 lines (largest: security/bot_scanner.py at 268 lines)
  - All files under 15 functions (largest: engine/simulation.py at 14)
  - All functions under 50 lines
- Fixed arch violation in `engine/simulation.py` (was 17 functions, over 15 limit):
  - Extracted `record_frame()`, `get_results()`, `export_replay()`, `get_track_pos()`, `_compute_positions()` into new `engine/replay.py` (111 lines, 5 functions)
  - Extracted `get_curvature_at()` into `engine/track_gen.py` (now 99 lines, 4 functions)
  - Removed 3 thin wrapper methods from RaceSim class: `get_track_pos`, `get_curvature_at`, `get_positions`
  - simulation.py reduced from 325 lines / 17 functions to 257 lines / 14 functions
- Created `tests/test_replay.py` (6 tests) for the new replay module
- Integration gate smoke test: `python play.py --track monza --laps 1 --no-browser` produces valid replay JSON with `track_name: monza`
- All engine exports verified importable and used in runtime code paths
- All public functions have callers outside tests

### Session: 2026-03-17 - T1.6 play.py --track and --list-tracks

- play.py already had full implementation from prior sessions (T1.7 CLI packaging wired --track/--list-tracks into play.py)
- `_print_tracks()` prints formatted table with Name, Country, Character columns plus "20 tracks available" count
- `_resolve_track(args)` handles None (procedural), "random" (random_track()), valid name (lowercase lookup), invalid name (error + exit 1)
- `main()` passes track_name to run_race(), prints note when --seed used with --track
- Added 3 new tests to `tests/test_play.py` (162 lines): test_list_tracks_shows_count, test_track_random_prints_selection, test_invalid_track_lists_available
- Total: 14 tests across 5 classes covering all 7 acceptance criteria
- 188/189 tests passing (1 pre-existing failure unrelated to T1.6), ruff clean

### Session: 2026-03-17 - T1.8 viewer.html track name in header

- Added dedicated `trackName` element in header between logo and race-info
- Track name reads `replay.track_name`, falls back to "Procedural Track" when absent
- Styled with `.track-name` class (16px, 600 weight, #ccc) and orange triangle marker via `.track-label`
- Race stats (car count, laps, frames) now displayed separately in existing `raceInfo` element
- No external dependencies added; all styling uses existing dark theme palette (#ff6600 accent, #ccc text)
- All 4 acceptance criteria met

### Session: 2026-03-17 - T1.5 Engine track integration (verification)

- T1.5 implementation was already complete from prior sessions (T1.2 decomposition wired tracks into race_runner.py)
- `engine/race_runner.py` (77 lines): `run_race()` accepts `track_name`, loads control points via `get_track()`, uses `laps_default` when laps not specified, falls back to procedural generation
- `engine/simulation.py` (326 lines): `RaceSim.__init__` stores `track_name`, `export_replay()` includes it in JSON
- `engine/__init__.py` (28 lines): re-exports `get_track`, `list_tracks`, `random_track` from tracks package
- `tests/test_engine_tracks.py` (191 lines): 10 tests across 6 classes covering all 7 acceptance criteria
  - TestNamedTrackIntegration (2): monza race completes, replay has track_name
  - TestLapsDefault (1): track's laps_default used when laps not specified
  - TestExplicitLapsOverride (1): explicit laps=2 overrides track default
  - TestProceduralFallback (3): no track_name works, track_name is None in replay, default 3 laps
  - TestReplayTrackName (1): replay JSON always has track_name key
  - TestInvalidTrackName (2): KeyError raised for bad track name
- All 10 T1.5 tests passing, 185/186 total passing (1 pre-existing failure unrelated to T1.5)
- Ruff clean on all engine files and test file

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

T3.8 done. All 5 seed cars rewritten with pit stop, fuel, lateral, and engine mode strategies. Ready for next task.

## Blockers

None currently.

## Notes

- engine.py decomposed into engine/ package (T1.2), all files under 400 lines
- npc-wars bot_scanner.py and sandbox.py to be copied and adapted (T1.3, T1.4)
- Trello is not connected for this project (trello.enabled: false)
- No external dependencies allowed -- Python stdlib only
