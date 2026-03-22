# Current State

> Last updated: 2026-03-22 T27.7 complete — Glitch + code quality wired into race loop.

## Active Plan

**Plan:** NPC Race v3 — Build a Car Out of Code (Master Plan)
**Reference:** docs/proposal-npc-race-v3.md + npc-race-v3.1-proposal.md

## Current Focus

### Sprint 26: Physics Bug Fixes — BOTH GATES PASS ✓
Fixed 2 root-cause bugs (ERS lap reset, lateral G formula) + 1 calibration (cornering wear rate).

**1-lap**: 3.47s spread, 80.83s baseline, 4/9 parts above 0.3s. Gate PASS.
**5-lap**: 19.50s spread, 12.5% tire wear, ers_deploy +0.60s, ers_harvest +0.77s. Gate PASS.

### Follow-up Task (not blocking)
Redesign suspension and differential optimized test variants for correct lateral G physics. Both show negative sensitivity because the "optimized" strategies were designed for 50x-wrong G values. ~30 min per part.

### Future Phases
- Phase 2: Code quality → reliability system
- Phase 3: Multi-file car project loader
- Phase 4: League system + live code terminal + TRON viewer

## What Was Just Done

- **T27.7 COMPLETE**: Wired `GlitchEngine` + `compute_reliability_score` into the race loop. Added `_apply_glitch` helper to `safe_call.py` (115 lines). `_safe_call_with_timeout` now accepts optional `glitch_ctx` and applies glitch checks internally. `run_efficiency_tick` passes glitch context through all 10 part calls + calls `tick_glitches` at end. `PartsRaceSim.__init__` creates `GlitchEngine(scale=0.3)` and computes per-car reliability from `_source` (defaults to 1.0). 11 tests in `tests/test_glitch_wiring.py` (197 lines). All 72 related tests pass, ruff clean, `efficiency_engine.py` at 398 lines.

- **T27.4 + T27.5 COMPLETE**: Added `engine/code_quality.py` (119 lines) with 5 AST-based metrics: cyclomatic complexity, cognitive complexity, function lengths, type hint coverage, and aggregate reliability score (0.50-1.00). 13 tests in `tests/test_code_quality.py` (122 lines). All passing, ruff clean, under size limits.

- **Sprint 26 COMPLETE**: Fixed ERS per-lap counter reset (deploy/harvest caps were never resetting — ERS dead after lap 1). Fixed lateral G formula (was 50x too low — `curv*speed/150` replaced with `v²κ/g`). Calibrated cornering wear rate for real G values (0.0003→0.00009). Reduced diff understeer coefficient (0.40→0.10). 5-lap spread jumped from 10.0s to 19.5s. ERS deploy from -0.57s to +0.60s. Tire wear from 1.5% to 12.5%.

- **Sprint 25**: Physics-emergent efficiency. Removed 5 artificial hacks. 1-lap gate pass at 4.03s (with old lateral G).

- **Sprint 24**: Built multiplicative efficiency engine (efficiency_engine.py).

## Completed Sprints

### Sprints 1-9 — Core Game Engine ✓
Tracks, viewer, realism (tires, fuel, DRS, setup), dashboard, drama engine (collisions, safety car). All done.

### Sprints 10-11 — Weather + ERS + Brakes ✓
Weather model, wet compounds, ERS model, brake temperature model, simulation extraction. All done.

### Sprints 17-23 — Parts Engine Foundation ✓
WebSocket streaming, driver model, physics recalibration, parts API (10 parts), physics engines (powertrain, chassis, hybrid), parts runner, parts simulation, Phase 0 baseline. All done.

### Sprint 24 — Multiplicative Efficiency Engine ✓
efficiency_engine.py with per-part efficiency factors, 1ms watchdog, t-1 state. Initial gate pass.

### Sprint 25 — Physics-Emergent Efficiency ✓
Replaced all artificial hacks: heat model fix, removed prescribed efficiencies, removed ^1.3 amplification, replaced profile speed hack with grip_factor, wired brake_bias/diff/tire thermal. 1-lap gate PASS. 5-lap verification flagged 4 parts for future fix.

## Key Metrics

- **Monza 1-lap baseline: 86.43s** (physics-emergent, naive defaults)
- **Monza 1-lap optimized: 82.40s** (4.03s spread from physics)
- **6/9 parts above 0.3s sensitivity** (gearbox, suspension, cooling, fuel_mix, differential, ers_deploy)
- **efficiency_engine.py: 398 lines** | **safe_call.py: 115 lines**

## Blockers

None.

## Notes

- ers_deploy **-0.57s at 5 laps = RED FLAG** — fix first in next physics sprint
- Tire wear 0.015 after 5 laps = decorative — needs 5-15% for engine_map to matter
- brake_bias lockup produces 2% reduction — tuning issue, lower priority
- Trello not connected | Python stdlib only | No external dependencies
