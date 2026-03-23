# NPC Race v3 — Progress Report

> Date: 2026-03-23 | 31 sprints completed | 38 commits on current branch

---

## Project Summary

NPC Race is a competitive coding game where players write Python functions that control the mechanical systems of an F1 race car. Every function is a real car part — engine map, gearbox, suspension, cooling, differential, and more. The physics simulation calls each function 30 times per second. Better engineering decisions, expressed as better code, produce a faster, more reliable car.

The game replaced a v1/v2 system where players configured 5 abstract stats and wrote a single strategy function. That was a configuration game, not a coding game. Changing player code by meaningful amounts produced 0.0-0.3 seconds of lap time difference. The physics didn't care what the code did.

v3 changed the architecture so that every part's decision passes through real physics — traction circles, thermodynamics, aerodynamic force models — and the consequences compound multiplicatively across a race. A 5.80-second spread now separates naive defaults from optimized code on a single Monza lap. Over 5 laps, compound effects (tire wear, ERS cycling, fuel management) push the gap to 17.77 seconds.

---

## What's Built

### Codebase Scale

| Metric | Count |
|--------|-------|
| Python source files | 175 |
| Engine modules | 49 |
| Test files | 119 |
| Total tests | 1,974 |
| Sprints completed | 31 |

### Phase Completion

| Phase | Description | Status | Sprints |
|-------|------------|--------|---------|
| Phase 0 | Baseline measurement | ✅ Done | S23 |
| Phase 1 | Core physics engine | ✅ Closed | S24-28 |
| Phase 2 | Code quality → reliability | ✅ Done | S27 |
| Phase 3 | Multi-file car project loader | ✅ Done | S29 |
| Phase 4a | League system | ✅ Done | S30 |
| Phase 4b | Viewer additions | ✅ Done | S31 |
| Phase 5 | Infrastructure | Not started | S32-33 |

### Core Systems

**Physics Engine** (Sprints 24-28)
- Multiplicative efficiency model: 3 efficiency factors (gearbox, cooling, fuel_mix) multiply into acceleration
- 6 additional parts work through direct physics consequences (suspension→downforce→grip, differential→traction, ERS→battery management, etc.)
- Real lateral G (1.7-3.0G in corners), realistic engine thermal model, 12.5% tire wear over 5 laps
- Monza baseline: 81.13s (real F1 is ~80s). Optimized: 75.33s. Spread: 5.80s.

**Code Quality System** (Sprint 27)
- AST-based metrics: cyclomatic complexity, cognitive complexity, function lengths, type hints
- Reliability score (0.50-1.00) computed per car from source code
- Glitch engine: per-tick per-part reliability rolls. Failed roll → part output replaced with default
- `reliability_scale` knob (0.0-2.0) for tuning. Default 0.3.

**Car Project Loader** (Sprint 29)
- Directory-based car projects (one file per part function)
- Partial implementation: 3 parts detected → remaining 7 filled with defaults
- Deep import graph scanner: catches `gearbox.py → helpers/utils.py → os.subprocess`
- Default template (`cars/default_project/`) with 3 F3 parts + README

**League System** (Sprint 30)
- F3 (gearbox, cooling, strategy) → F2 (+suspension, ers_deploy, fuel_mix) → F1 (all 10) → Championship (all 10 + quality gate)
- Advisory quality reports for F3/F2 (inform, never block)
- Enforced quality gates for F1/Championship (CC < 15, ruff clean, reliability ≥ 0.88)
- Auto-detection from loaded parts. CLI `--league` flag.

**Viewer** (Sprint 31)
- Call log export at 1Hz in replay JSON
- Live code terminal: part calls color-coded by status (ok/clamped/glitch/error)
- Code grade card: letter grade (A-D) + reliability percentage bar

### Sensitivity Distribution (Final, Sprint 28)

| Part | 1-Lap Gain | Domain | Mechanism |
|------|-----------|--------|-----------|
| gearbox | +1.40s | Powertrain | RPM vs torque curve |
| suspension | +1.00s | Aero | Downforce vs drag tradeoff |
| cooling | +0.87s | Aero | Cooling drag vs engine temp |
| ers_deploy | +0.80s | Hybrid | Battery conservation |
| fuel_mix | +0.73s | Powertrain | Rich mixture torque bonus |
| differential | +0.37s | Chassis | Speed-dependent optimal lock |
| engine_map | 0.00s | Powertrain | Multi-lap (tire wear) |
| brake_bias | 0.00s | Chassis | Multi-lap (lockup penalty) |
| ers_harvest | 0.00s | Hybrid | Multi-lap (harvest cycling) |

---

## What's Left

### Phase 5: Infrastructure (2 sprints)

**Sprint 32 — Submission Pipeline**
Player pushes a car project → engine evaluates (security scan + quality score + race) → results returned. This is the minimum viable product loop. No API keys, no scheduling — just "submit code, get results."

**Sprint 33 — Onboarding + Leaderboard**
Player discovery flow (README, signup, first race). Persistent leaderboard. Season tracking. This is the growth layer that turns the game into a product.

### Known Technical Debt

| Item | Impact | Priority |
|------|--------|----------|
| 3 parts at 0.00s 1-lap sensitivity | engine_map, brake_bias, ers_harvest only matter at race distance | Low — documented, known fixes |
| TRON car diagnostic (dropped from S31) | Wireframe car with part pulses/glitch flashes | Low — experience polish |
| Suspension/diff physics rewiring incomplete | Work through efficiency product removal but need corner-specific traction model | Low — contribute +2.8s through interaction |
| `run_efficiency_tick` at ~150 lines | Above 50-line function limit | Medium — extract more helpers |

---

## Key Decisions Made

1. **Physics-emergent, not prescribed.** Efficiency scores that conflicted with physics were removed (engine_map, ERS deploy, suspension, differential). Speed differences emerge from real force chains, not hardcoded optimals.

2. **The 10-second single-lap spread was a fantasy.** Real F1 driver-to-driver differences are 2-5s per lap. The game produces 5.80s from honest physics. The depth comes from compound effects over race distance (17.77s at 5 laps), not from inflating single-lap numbers.

3. **Defaults should be naive, not semi-competent.** The spread comes from making defaults clearly suboptimal (full torque, late shifts, max deploy, fixed values), not from amplifying physics consequences.

4. **Advisory before enforced.** F3/F2 leagues show code quality costs without blocking entry. Enforced gates only at F1/Championship. This teaches quality without frustrating beginners.

5. **One change, one measurement.** After Sprint 25's calibration loops (7 hours going in circles), the discipline was established: fix physics, measure once, calibrate once, stop. Sprint 26 applied this successfully (3 commits, both gates passing).

---

## The Game Loop (End to End)

A player today can:

1. Fork `cars/default_project/` (gearbox, cooling, strategy)
2. Write better part functions (shift at peak torque, optimize cooling tradeoff)
3. Run `npcrace run --car-dir my_car/ --track monza --laps 5`
4. The loader detects which parts are implemented, fills defaults for the rest
5. The league system auto-detects F3 tier from 3 loaded parts
6. The code quality system scores reliability from AST metrics
7. The physics engine calls their functions 30x/second with real physics consequences
8. The glitch engine randomly replaces outputs for low-reliability code
9. The viewer shows their code executing with color-coded call status
10. Results show lap times, positions, and compound effects over the race

What's missing: the submission pipeline (how they submit remotely) and the leaderboard (how they see standings). That's Phase 5.
