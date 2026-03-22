# NPC Race: Current State vs Proposed State

> Updated: 2026-03-21 after Sprint 26 (physics bug fixes)

## Current State (Sprints 1-26)

### What We Have

**Engine:** 1,700+ tests. 30+ modules. 20 tracks. 5 seed cars. Simulation at 30 Hz. WebSocket viewer with pit wall dashboard.

**Car System:** Two coexisting systems:
- **Legacy (v1):** 5 abstract stats + `strategy()` function. Still used by the old `RaceSim`.
- **Parts (v3):** 10 part functions + efficiency engine + 3 physics engines. `PartsRaceSim` is the primary system for v3.

**Physics (v3 — Sprints 24-26):**
- Multiplicative efficiency engine (`efficiency_engine.py`) — 5 efficiency factors multiply into a product that scales acceleration
- Physics-derived grip_factor scales corner speed (downforce, tire grip, understeer)
- Real lateral G formula (v²κ/g) — cornering forces at 1.7-3.0G
- Realistic engine thermal model (equilibrium ~110°C with moderate cooling)
- ERS battery with per-lap deploy/harvest caps and lap reset
- Tire wear: 12.5% after 5 laps with real F1 degradation rates
- Traction circle with front/rear brake force splitting (lockup model)
- Differential understeer reduces corner speed through physics

**Sensitivity (Sprint 26 results):**
- 1-lap: 3.47s spread, 80.83s baseline, 4/9 parts above 0.3s
- 5-lap: 19.50s spread, compound effects working across laps
- ERS deploy/harvest alive at 5 laps (+0.60s, +0.77s)
- No artificial hacks (no prescribed optimals, no amplification, no profile speed hack)

### What Works

| Component | Status | Notes |
|-----------|--------|-------|
| 20 tracks with real-world data | ✅ Working | Monza lap time ~81s (real F1 ~80s) |
| 5 seed cars | ✅ Working | Legacy format + parts defaults |
| Efficiency engine | ✅ Working | 5 factors: gearbox, suspension, cooling, diff, fuel_mix |
| Grip factor (corner speed) | ✅ Working | Downforce + tire grip → physics-derived corner speed |
| ERS battery cycling | ✅ Working | Deploy/harvest with per-lap caps, lap reset |
| Tire wear model | ✅ Working | 12.5% after 5 laps, grip degrades meaningfully |
| Traction circle | ✅ Working | Real lateral G, wheelspin detection, brake lockup |
| 3 physics engines | ✅ Working | Powertrain, chassis, hybrid |
| Speed profile + driver model | ✅ Working | Pre-computes optimal speed |
| WebSocket viewer | ✅ Working | Dashboard, telemetry, timing tower |
| Narrative engine | ✅ Working | Events, commentary, race reports |
| CI pipeline | ✅ Working | Fast tests + lint on push |
| Bot scanner security | ✅ Working | Sandboxed execution |

### What Doesn't Work Yet

| Component | Status | Problem |
|-----------|--------|---------|
| Code quality → reliability | ❌ Not built | No AST analysis, no glitch system |
| Multi-file car projects | ❌ Not built | Cars are single files |
| League system | ❌ Not built | No progression, no part restrictions |
| Live code terminal | ❌ Not built | Viewer doesn't show code executing |
| TRON car diagnostic | ❌ Not built | No wireframe car status display |
| Evaluation pipeline | ❌ Not built | No submission flow, no quality scoring |
| Suspension optimized variant | ⚠️ Stale | Designed for 50x-wrong lateral G, shows -0.83s |
| Differential optimized variant | ⚠️ Stale | Strategy wrong for real traction model, shows -0.53s |
| Engine_map sensitivity (1-lap) | ⚠️ Limited | 0.00s at 1 lap (tire wear too slow for 1-lap effect) |
| Brake_bias sensitivity | ⚠️ Weak | 0.00s — lockup model functional but penalty gentle |

---

## Proposed State (v3.1)

### Progress Against v3.1 Proposal

| Phase | Status | What Was Done |
|-------|--------|---------------|
| Phase 0: Baseline | ✅ Done (S23) | Measured -0.07s spread — proved v2 was broken |
| Phase 1: Core physics | ✅ Done (S24-26) | Efficiency engine, grip factor, lateral G, ERS, tire wear |
| Phase 2: Code quality | ❌ Next | AST analyzer, reliability scoring, glitch engine |
| Phase 3: Car loader | ❌ Future | Multi-file car project support |
| Phase 4: Leagues + viewer | ❌ Future | League system, code terminal, TRON diagnostic |
| Phase 5: Infrastructure | ❌ Future | Submission pipeline, onboarding |

### Sensitivity Evolution

| Metric | Phase 0 (v2) | Phase 1 (S24) | Phase 1 (S25) | Phase 1 (S26) |
|--------|-------------|---------------|---------------|---------------|
| Baseline lap | 87.73s | — | 86.43s | 80.83s |
| Total spread | -0.07s | 10.77s* | 4.03s | 3.47s |
| Parts > 0.3s | 0/9 | 6/9* | 6/9 | 4/9 |
| Lateral G | 0.04G | 0.04G | 0.04G | 1.7-3.0G |
| Tire wear (5 lap) | — | — | 1.5% | 12.5% |
| ERS deploy (5 lap) | — | — | -0.57s | +0.60s |
| 5-lap spread | — | — | 10.0s | 19.5s |
| Physics honest? | Yes (but dead) | No (hacks) | Yes | Yes |

*Sprint 24 numbers used artificial hacks (prescribed optimals, ^1.3 amplification, profile speed hack). All removed in Sprint 25.

### Remaining Effort

| Task | Sprints | Depends On |
|------|---------|------------|
| Suspension/diff variant redesign | <1 | Nothing (stale test fixtures) |
| Phase 2: Code quality system | 1 | Nothing (physics stable) |
| Phase 3: Car project loader | 1 | Phase 2 |
| Phase 4: Leagues + viewer | 2 | Phase 3 |
| Phase 5: Infrastructure | 1-2 | Phase 4 |
| **Total remaining** | **5-7 sprints** | |
