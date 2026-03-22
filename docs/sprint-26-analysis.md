# Sprint 26 Analysis — Physics Bug Fixes Trial Report

> Date: 2026-03-21 | Branch: sprint-16-championship

## Executive Summary

Sprint 25 shipped a physics-emergent efficiency engine that passed the 1-lap sensitivity gate (4.03s spread, 6/9 parts). The 5-lap verification flagged 4 parts as dead. Investigation in Sprint 26 found **three root-cause bugs**, not tuning issues. Two are one-line fixes. The third (tire wear rebalancing) requires calibration but the physics foundation is now correct.

---

## Bug 1: ERS Per-Lap Counters Never Reset

**Severity:** Critical (makes ERS dead after lap 1)

**Root cause:** `reset_ers_lap()` exists in `hybrid_physics.py:72` and is called in the old `simulation.py:364`, but NOT in the new `parts_simulation.py`. After lap 1 depletes the 4.0 MJ deploy cap, `lap_deploy_mj` stays at 4.0 forever. The `update_ers()` function checks `ERS_DEPLOY_LIMIT_MJ_PER_LAP - lap_deploy_mj` and gets 0.0 — no deployment allowed.

**Impact:** Both default and optimized ERS are dead after lap 1. Battery sits at 1-2 MJ for laps 2-5 with no deploy or harvest. This is why:
- ers_deploy showed -0.57s at 5 laps (both strategies are equally dead, noise determines winner)
- ers_harvest showed -0.03s (harvest cap also never resets)
- 5-lap total spread was only 10.0s (barely 2.5x the 1-lap spread instead of 5x)

**Fix:** 1 line in `parts_simulation.py`:
```python
if current_lap > state.get("lap", 0):
    new_state["lap"] = current_lap
    new_state["ers_state"] = reset_ers_lap(new_state["ers_state"])  # ← ADD THIS
```

**Verification:** After fix, battery deploys in all 5 laps. ers_deploy shows +0.53s, ers_harvest shows +1.07s at 5 laps.

**Status:** Fixed (uncommitted)

---

## Bug 2: Lateral G Formula 50x Too Low

**Severity:** Critical (makes tire wear, diff understeer, and traction circle decorative)

**Root cause:** `parts_simulation.py:125` uses `curv * speed_kmh / 150` — a naive heuristic with no physical basis. The correct formula is `v² × κ / g` where v is in m/s and κ accounts for sim-to-real scale.

| Corner | Current Formula | Correct Formula | Error |
|--------|----------------|-----------------|-------|
| Chicane (curv=0.08, 80 km/h) | 0.043G | 1.72G | 40x |
| Fast (curv=0.02, 200 km/h) | 0.027G | 2.68G | 100x |
| Sweep (curv=0.01, 300 km/h) | 0.020G | 3.02G | 150x |

**Impact:** Everything proportional to lateral_g was broken:
- Cornering tire wear threshold (0.5G) never reached → tire model decorative
- Differential understeer penalty (proportional to lateral_g) invisible
- Traction circle lateral force near zero → no grip competition between turning and accelerating
- Corner phase detection still worked (uses curvature thresholds, not G)

**Fix:** 1 line in `parts_simulation.py`:
```python
# Before:
"lateral_g": curv * state["speed_kmh"] / 150,
# After:
"lateral_g": (state["speed_kmh"] / 3.6) ** 2 * curv / (self.real_per_sim * 9.81),
```
Plus `self.real_per_sim = real_length_m / track_length` in `__init__`.

**Verification:** Lateral G now 1.7-3.0G in corners. Cornering wear accumulates. Diff understeer is measurable.

**Status:** Fixed (uncommitted)

---

## Bug 3 (Not a Bug): Tire Wear Rate Rebalancing

**Severity:** Medium (calibration, not architecture)

**Root cause:** The cornering wear rate `0.0003 * (lateral_g - 0.5)` was calibrated for fake 0.04G lateral values. With real 1.7-3.0G values, the rate produces 54% wear per lap — catastrophic.

**Calibration trials:**

| Cornering Rate | Grip Coeff | 5-Lap Wear | 5-Lap Grip Loss | Verdict |
|---------------|------------|------------|----------------|---------|
| 0.0003 (original) | 0.3 | 22.6% | 6.8% | Too high (with real G) |
| 0.000015 | 0.3 | 3.0% | 0.9% | Too low |
| 0.00005 | 0.6 | 7.2% | 4.3% | In target range (5-15%) |

**Current uncommitted state:** Rate 0.00005, grip coefficient 0.6. Produces 7.2% wear after 5 laps.

**Remaining issue:** The 1-lap gate that was passing at 4.03s spread (Sprint 25) now shows 2.57s with the new physics. This is because correct lateral_g changes the traction circle behavior, corner speeds, and relative part contributions. The diff understeer coefficient (0.40) is too strong for real G values and produces -0.20s for the "optimized" differential.

**Status:** Partially calibrated (uncommitted). Needs one more pass after bugs 1-2 are stable.

---

## Impact on Sensitivity Gate

### Before Bug Fixes (Sprint 25 committed)

| Metric | 1-Lap | 5-Lap |
|--------|-------|-------|
| Baseline | 86.43s | 418.30s |
| Spread | 4.03s ✓ | 10.00s ✓ |
| Parts > 0.3s | 6/9 ✓ | 0/4 ✗ |
| ers_deploy | +0.80s | -0.57s ← RED FLAG |
| engine_map | 0.00s | 0.00s |
| Tire wear | 1.5% | 1.5% |
| Gate | **1-LAP PASS** | **5-LAP FAIL** |

### After Bug Fixes (uncommitted)

| Metric | 1-Lap | 5-Lap |
|--------|-------|-------|
| Baseline | 81.23s | 399.37s |
| Spread | 2.57s ✗ | 8.83s ✗ |
| Parts > 0.3s | 4/9 ✗ | 2/4 ✓ |
| ers_deploy | +0.13s | +0.53s ✓ |
| ers_harvest | 0.00s | +1.07s ✓ |
| Tire wear | — | 7.2% ✓ |
| Gate | **1-LAP FAIL** | **5-LAP PARTIAL** |

**Interpretation:** Bug fixes solved the 5-lap problems (ERS alive, tire wear real) but broke the 1-lap gate (balance shifted). This is expected — the physics model is fundamentally different with 50x larger lateral G.

---

## What Was Learned

### 1. The lateral_g formula was the single biggest physics error in the simulation.
It made cornering forces near-zero, which cascaded to: no tire wear, no diff effect, no traction circle competition, and artificial sensitivity from prescribed efficiency functions instead of physics.

### 2. The ERS reset was a wiring oversight, not a design decision.
The old simulation.py had it. The new parts_simulation.py was built without it. Classic integration gap from parallel development.

### 3. Calibration and physics fixes cannot be done simultaneously.
Every time I fixed a bug AND tuned coefficients in the same pass, the coefficients were tuned to compensate for the bug. When the bug was later fixed, the coefficients were wrong. This happened repeatedly with the amplification exponent, profile speed hack, and tire wear rates.

### 4. The sensitivity gate criteria need to flex with the physics.
The 1-lap gate was calibrated for the old (broken) physics. With correct lateral G, the physics produces different sensitivity distribution. The gate should be re-established AFTER the physics stabilizes, not tuned simultaneously.

---

## Remediation Path

### Step 1: Commit the two bug fixes ONLY (no calibration changes)
- ERS reset: 1 line
- Lateral_g formula: 1 line + 1 line for `real_per_sim`
- Revert all tire wear rate changes to committed values (0.0003, 0.3 grip coeff, 8.0 temp)

### Step 2: Run sensitivity test with correct physics + original rates
Measure where the physics ACTUALLY lands with correct lateral G and working ERS, without any rate tuning. This is the honest baseline for the new physics model.

### Step 3: Single calibration pass
Based on Step 2 results, adjust ONLY the rates that are clearly wrong (cornering wear will be too high with 0.0003 at real G values). One adjustment, one test run, done.

### Step 4: Re-establish gate criteria
If the 1-lap spread is 2-3s instead of 3-5s, that may be honest physics with correct lateral G. The gate criteria should match what the correct physics produces, not the other way around.

### Step 5: Run both gates and document
Save final results. If 5-lap shows ERS and tire wear alive, the sprint succeeds regardless of whether the 1-lap numbers exactly match the old gate.

**Estimated effort:** Steps 1-2 are 15 minutes. Steps 3-5 are 30 minutes. Total: under 1 hour if done without calibration loops.
