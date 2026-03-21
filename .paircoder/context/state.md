# Current State

> Last updated: 2026-03-21 Sprint 25 complete — physics-emergent efficiency.

## Active Plan

**Plan:** NPC Race v3 — Build a Car Out of Code (Master Plan)
**Reference:** docs/proposal-npc-race-v3.md + npc-race-v3.1-proposal.md

## Current Focus

### Sprint 25: Physics-Emergent Efficiency — 1-LAP GATE PASS ✓
Replaced 5 artificial hacks with physics-emergent behavior. Results: 4.03s spread from 86.43s baseline, 6/9 parts above 0.3s, no hacks.

### 5-Lap Verification — 4 parts flagged for future fix
- ers_deploy: **-0.57s (RED FLAG)** — optimized loses time. Battery cycling equilibrium.
- engine_map: 0.00s — tire wear 0.015 after 5 laps, model has no teeth.
- brake_bias: 0.03s — lockup produces only 2% braking reduction.
- ers_harvest: -0.03s — noise.

### Next Sprint Priorities
1. **Fix ers_deploy negative sensitivity** — player should never lose time by being smarter
2. **Tire wear model** — needs 5-15% wear after 5 laps, not 1.5%
3. Then reassess brake_bias, ers_harvest

### Future Phases
- Phase 2: Code quality → reliability system
- Phase 3: Multi-file car project loader
- Phase 4: League system + live code terminal + TRON viewer

## What Was Just Done

- **Sprint 25 COMPLETE**: Physics-emergent efficiency. Removed 5 artificial hacks, fixed 3 bugs, wired 3 physics gaps. 1-lap gate PASS: 4.03s spread, 6/9 parts above 0.3s, baseline 86.43s. 5-lap: 10.0s total, 4 multi-lap parts flagged (ers_deploy -0.57s red flag, tire wear decorative).

- **Sprint 24 COMPLETE**: Built multiplicative efficiency engine (efficiency_engine.py). Initial gate with artificial hacks, subsequently replaced in Sprint 25.

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
- **efficiency_engine.py: 433 lines** | **safe_call.py: 86 lines**

## Blockers

None.

## Notes

- ers_deploy **-0.57s at 5 laps = RED FLAG** — fix first in next physics sprint
- Tire wear 0.015 after 5 laps = decorative — needs 5-15% for engine_map to matter
- brake_bias lockup produces 2% reduction — tuning issue, lower priority
- Trello not connected | Python stdlib only | No external dependencies
