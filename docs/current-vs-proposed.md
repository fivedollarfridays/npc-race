# NPC Race: Current State vs Proposed State

## Current State (v2, Sprints 1-22)

### What We Have

**Engine:** 1,759 tests. 30+ modules. 20 tracks. 5 seed cars. Simulation runs at 30 Hz. WebSocket streaming viewer with pit wall dashboard.

**Car System:** Two coexisting systems, neither complete:
- **Legacy (v1):** 5 abstract stats (POWER/GRIP/WEIGHT/AERO/BRAKES, 100-point budget) + `strategy()` function. Still the primary system used by the race runner. Cars are single files under 100 lines.
- **Parts (v2):** 10 part functions (engine_map, gearbox, etc.) + 3 physics engines (powertrain, chassis, hybrid) + parts runner sandbox. Built in Sprints 20-21 but not yet the primary system. `PartsRaceSim` exists as a separate class.

**Physics:** Power-based speed model (F=P/v) with traction circle. Simplified Pacejka-like tire model. Real F1 constants. Monza lap times: 82-86s (target ~80s). Top speed: 333-362 km/h (realistic). The physics is CORRECT but the sensitivity test shows near-zero impact from player code changes.

**The Critical Gap:** Parts exist but don't meaningfully affect lap time. Changing one part function by a lot changes lap time by 0.0-0.3s. The physics engine computes speed independently of part outputs. There is no multiplicative model. Code quality has zero effect on race performance.

**Viewer:** Dashboard with timing tower, telemetry panels, speed/tire/gap charts, TV Director camera, spatial audio, narrative engine. No live code terminal. No TRON car diagnostic. No code quality display.

**Infrastructure:** GitHub CI (fast/slow split), branch protection, WebSocket streaming, championship mode with seasons/points/development. All working.

### What Works

| Component | Status | Notes |
|-----------|--------|-------|
| 20 tracks with real-world data | ✅ Working | Monza recently redesigned with longer straights |
| 5 seed cars | ✅ Working | Legacy format, hardware specs added |
| Race simulation (legacy) | ✅ Working | Produces races with results, narrative, replay |
| Parts runner sandbox | ✅ Working | Calls 10 functions per tick, logs calls, handles errors |
| 3 physics engines | ✅ Working | Powertrain, chassis, hybrid — correct equations |
| Speed profile + driver model | ✅ Working | Pre-computes optimal speed, provides throttle/brake |
| WebSocket viewer | ✅ Working | Streams frames live, dashboard layout |
| Narrative engine | ✅ Working | Detects events, generates commentary, race reports |
| Championship mode | ✅ Working | Seasons, points, car development |
| CI pipeline | ✅ Working | Fast tests (~3 min) on push, full suite on labeled PRs |
| Bot scanner security | ✅ Working | Sandboxed execution, import restrictions |

### What Doesn't Work

| Component | Status | Problem |
|-----------|--------|---------|
| Part sensitivity | ❌ Failed | Changing parts produces 0.0-0.3s effect (target: 0.5-1.5s each) |
| Multiplicative model | ❌ Not built | Parts add, not multiply. No compound effects. |
| Code quality → performance | ❌ Not built | Code quality has zero effect on car behavior |
| Multi-file car projects | ❌ Not built | Cars are single files |
| League system | ❌ Not built | No progression, no part restrictions |
| Live code terminal | ❌ Not built | Viewer doesn't show code executing |
| TRON car diagnostic | ❌ Not built | No wireframe car status display |
| Part coupling | ❌ Broken | Engine_map doesn't affect gearbox, ERS doesn't add power to speed, cooling doesn't affect drag in speed calc |
| Evaluation pipeline | ❌ Not built | No submission flow, no quality scoring |
| Player onboarding | ❌ Not built | No default car repo, no README, no email signup |

---

## Proposed State (v3)

### The Shift

| Dimension | v2 | v3 |
|-----------|----|----|
| **Game model** | Configure stats, write strategy | Write code for 10 car parts |
| **What player codes** | 1 function (strategy) | 10 functions (each IS a car part) |
| **Physics sensitivity** | ~0.0s per part change | ~0.5-1.5s per part change |
| **Combination model** | Additive (A + B + C) | Multiplicative (A × B × C) |
| **Code quality effect** | None | Reliability score → glitch rate |
| **Car file format** | Single .py file, <100 lines | Multi-file project directory |
| **Difficulty progression** | None | F3 (3 parts) → F2 (6) → F1 (10) → Championship |
| **Evaluation** | Bot scanner only | Security + quality + architecture + reliability |
| **Viewer** | Pit wall dashboard | + live code terminal + TRON diagnostic |
| **Target audience** | Anyone | Engineers who want depth (with accessible entry via F3) |
| **Total spread** | ~3s (from driver model) | ~10s (from code quality × part optimization) |

### What Gets Built (New)

| Module | What It Does | Why It's Needed |
|--------|-------------|----------------|
| Refactored `parts_runner.py` | Real physics coupling, multiplicative efficiency | Core gap: parts must affect speed |
| `engine/code_quality.py` | AST-based quality analysis → reliability score | Code quality = car reliability |
| `engine/car_project_loader.py` | Load multi-file car projects | Modular code > monolithic |
| `engine/league_system.py` | Part restrictions per tier, quality gates | Accessibility + progression |
| `viewer/js/code-terminal.js` | Show player code executing in real-time | The game's signature experience |
| `viewer/js/car-diagnostic.js` | TRON wireframe car status | Visual feedback per part |
| `scripts/sensitivity_test.py` | Verify per-part impact + interactions | Calibration verification |
| Default car template repo | Open source onboarding project | Player entry point |
| Evaluation pipeline | Security → quality → reliability → race | Submission flow |

### What Gets Kept (Existing)

| Module | Status | Changes Needed |
|--------|--------|---------------|
| 20 tracks | Keep as-is | Monza already redesigned |
| Powertrain physics | Keep | Wire outputs INTO speed computation |
| Chassis physics | Keep | Wire traction circle INTO acceleration |
| Hybrid physics | Keep | Wire ERS power INTO drive force |
| Speed profile + driver model | Keep | Provides throttle/brake demands |
| Narrative engine | Keep as-is | Works with any sim class |
| Sound engine | Keep as-is | Independent of physics |
| WebSocket streaming | Keep | Extend to include part call logs |
| Championship mode | Keep | Works with any sim class |
| CI pipeline | Keep as-is | |
| Bot scanner | Extend | Scan directories, not just single files |

### What Gets Replaced

| Old | New | Why |
|-----|-----|-----|
| Legacy 5-stat car system | Multi-file car projects with 10 part functions | The game IS the code |
| `simulation.py` as primary race runner | `PartsRaceSim` as primary | Parts-driven physics |
| Fixed reliability (no code quality effect) | Reliability from AST quality analysis | Better code = better car |
| Additive part effects | Multiplicative efficiency model | Compound optimization depth |
| Single car template | Open source car project template | Onboarding + modular code |

---

## The Gap

| What Exists | What's Needed | Gap Size |
|-------------|--------------|----------|
| Parts runner calls 10 functions | Parts outputs must AFFECT speed multiplicatively | Large — core architecture change |
| Physics engines compute correct forces | Forces must flow FROM part decisions, not around them | Medium — rewiring, not rewriting |
| Quality metrics computable from AST | Need `code_quality.py` + reliability + glitch system | Medium — new module |
| Viewer shows telemetry | Need live code terminal + TRON diagnostic | Medium — new JS modules |
| Single-file cars | Need directory-based car loader | Small — loader extension |
| No league system | Need league definitions + part restrictions | Small — new module |
| No evaluation pipeline | Need submission → evaluation → race flow | Medium — new infrastructure |
| No player onboarding | Need default car repo + documentation | Small — content creation |

### Estimated Effort

| Phase | Sprints | What |
|-------|---------|------|
| Phase 1: Core physics coupling | 2-3 | Multiplicative model, real part sensitivity |
| Phase 2: Code quality system | 1 | AST analyzer, reliability, glitches |
| Phase 3: Car project loader | 1 | Multi-file support, extended scanner |
| Phase 4: Leagues + viewer | 2 | League system, code terminal, TRON diagnostic |
| Phase 5: Infrastructure | 1-2 | Submission pipeline, onboarding |
| **Total** | **7-10 sprints** | |
