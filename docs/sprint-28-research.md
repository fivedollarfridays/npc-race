# Sprint 28 Research — Differential & Suspension Physics Rewiring

> Date: 2026-03-22 | Goal: Both parts produce positive 1-lap sensitivity through direct physics

---

## Problem Statement

Differential and suspension show negative individual sensitivity (-0.53s, -0.83s). Both were removed from the efficiency product in Sprint 27. They need to produce speed differences through direct physics chains, not efficiency scores.

**Target**: Each part produces +0.3s to +0.5s individual sensitivity on 1-lap Monza. Combined with the 4 working parts (gearbox, ERS deploy, cooling, fuel_mix), this gives 6+ parts above 0.3s.

---

## Part 1: Differential

### Current Physics Chain

```
lock_pct → compute_diff_effect()
  → traction_mult: 0.85 + lock/100 * 0.15   (affects acceleration via effective_traction)
  → understeer: lock/100 * lateral_g * 0.1    (affects corner speed via grip_factor × penalty)
```

### Root Cause: Understeer Penalty Too Weak

At lock=50, lateral_g=1.5G:
- understeer = 0.5 × 1.5 × 0.1 = 0.075
- penalty = max(0.90, 1.0 - 0.075 × 0.10) = 0.9925 (**0.75% grip loss**)

At lock=100, lateral_g=1.5G:
- understeer = 1.0 × 1.5 × 0.1 = 0.15
- penalty = max(0.90, 1.0 - 0.15 × 0.10) = 0.985 (**1.5% grip loss**)

The understeer penalty is effectively invisible (0.75-1.5%). Meanwhile, traction ranges from 0.85 (lock=0) to 1.0 (lock=100) — a 15% range. Traction always dominates understeer. Higher lock is always better for acceleration, and the understeer cost in corners is negligible.

### What Real F1 Differentials Do

| Corner Type | Speed | Lateral G | Optimal Lock | Why |
|-------------|-------|-----------|-------------|-----|
| Slow hairpin | 80 km/h | 1.5-2.5G | 20-30% | Need rotation. High lock = inside tire saturates = understeer |
| Medium corner | 150 km/h | 2.0-3.0G | 40-55% | Balance traction and rotation |
| Fast sweeper | 250 km/h | 2.5-4.0G | 55-70% | Need stability. Low lock = snap oversteer risk |
| Corner exit | varies | declining | 70-90% | Maximum traction for acceleration |

**Key insight**: The optimal lock is NOT constant. It varies with lateral G and corner type. A fixed value is always wrong somewhere.

### Remediation Path A: Strengthen Understeer Penalty

Make the understeer penalty proportional to lateral_g² (non-linear at high G):

```python
# Current (too weak):
understeer_penalty = max(0.90, 1.0 - understeer * 0.10)

# Proposed:
understeer_penalty = max(0.85, 1.0 - understeer * lateral_g * 0.08)
```

At lock=50, lateral_g=2.0G:
- understeer = 0.5 × 2.0 × 0.1 = 0.10
- penalty = 1.0 - 0.10 × 2.0 × 0.08 = 0.984 (**1.6% grip loss**)

At lock=80, lateral_g=2.0G:
- understeer = 0.8 × 2.0 × 0.1 = 0.16
- penalty = 1.0 - 0.16 × 2.0 × 0.08 = 0.974 (**2.6% grip loss**)

Still small. The traction benefit of lock=80 (0.97 vs 0.925) is 4.8%, which exceeds the 1% additional understeer cost.

**Verdict**: Strengthening the penalty alone won't create a crossover where lower lock is sometimes better.

### Remediation Path B: Phase-Dependent Traction Model

The traction formula `0.85 + lock * 0.15` gives MORE traction with MORE lock, always. In reality, too much lock at low speed + high G causes the inside tire to saturate. The formula should have a G-dependent optimal:

```python
def compute_diff_effect(lock_pct, lateral_g, speed_kmh):
    lock = lock_pct / 100.0
    # Optimal lock depends on cornering intensity
    # At high lateral G, excessive lock saturates inside tire
    optimal_lock = min(0.8, 0.3 + speed_kmh / 1000)  # 0.3 at 0 km/h, 0.6 at 300 km/h
    lock_excess = max(0, lock - optimal_lock)
    lock_deficit = max(0, optimal_lock - lock)

    # Traction: peaks at optimal_lock, decreases on either side
    traction = 1.0 - lock_deficit * 0.20 - lock_excess * 0.15
    traction = max(0.80, traction)

    # Understeer: increases with lock AND lateral G
    understeer = lock * lateral_g * 0.1
    return traction, understeer
```

At 100 km/h (slow corner), optimal_lock = 0.40:
- lock=50%: deficit 0, excess 0.10 → traction = 1.0 - 0.015 = 0.985
- lock=30%: deficit 0.10 → traction = 1.0 - 0.020 = 0.980
- lock=80%: excess 0.40 → traction = 1.0 - 0.060 = 0.940

At 300 km/h (fast sweeper), optimal_lock = 0.60:
- lock=50%: deficit 0.10 → traction = 1.0 - 0.020 = 0.980
- lock=60%: at optimal → traction = 1.0
- lock=80%: excess 0.20 → traction = 1.0 - 0.030 = 0.970

**This creates speed-dependent sensitivity**: fixed lock=50 is wrong at both slow corners (should be 40%) and fast corners (should be 60%). Only adaptive code finds the optimal.

**Verdict**: This is the correct fix. The traction formula needs a speed-dependent optimal, not a linear ramp.

### Remediation Path C: Corner-Phase Exit Boost

Keep the current linear traction model but add a specific exit-phase traction bonus for high lock:

```python
if corner_phase == "exit" and lock > 0.6:
    traction *= 1.0 + (lock - 0.6) * 0.1  # up to +4% traction on exit
```

**Verdict**: Too targeted. Doesn't address mid-corner behavior. Path B is more complete.

### Recommended: Path B (phase-dependent traction with speed-dependent optimal)

---

## Part 2: Suspension

### Current Physics Chain

```
ride_height → compute_ride_height_effect() → actual_rh + bottoming flag
           → compute_downforce(speed, cl, ride_height) → downforce_N
           → compute_grip_factor(tire_mu, downforce, mass, ..., baseline_rh=-0.3)
               → df_ratio = (weight + downforce) / (weight + baseline_downforce)
               → grip_factor ≈ 1.0 ± 1% (always near unity)
```

### Root Cause 1: Grip Factor Baseline Comparison

`compute_grip_factor` compares current downforce against baseline downforce (at ride_height=-0.3). Since weight (7800 N) dominates over downforce (2000-6000 N depending on speed), the ratio is always 0.98-1.02. The sensitivity is mathematically capped at ~2%.

At 200 km/h:
- weight = 7800 N
- downforce at rh=-0.3: ~3500 N, ground_mult=1.09
- downforce at rh=-0.5: ~3800 N, ground_mult=1.15
- df_ratio = (7800+3800)/(7800+3500) = 11600/11300 = 1.027

**2.7% grip change = ~1% corner speed change = ~0.4s per lap.** This should be visible but the sweep showed -0.83s for -0.4. Why?

### Root Cause 2: Missing Ride Height Drag

In real F1, lower ride height increases both downforce AND drag. The current model:
- `compute_downforce`: uses `ground_mult` based on ride_height ✓
- `compute_drag`: uses `cd` and `cooling_effort` only — **ride_height does NOT affect drag** ✗

This means lower ride height gives FREE downforce with NO drag penalty. But the sensitivity test shows lower ride height is SLOWER. The explanation: the efficiency product. When suspension efficiency was in the product (Sprint 25), the `sus_eff` value penalized non-optimal ride heights. After removing `sus_eff` from the product (Sprint 27), there's no penalty mechanism at all — the downforce gain should be free.

**So why is -0.4 slower than -0.3?** Let me trace through:
1. At -0.4: more compression at high speed → actual_rh further from baseline → grip_factor slightly > 1.0 → faster corners (tiny amount)
2. At -0.4: no extra drag (not modeled) → same straight speed
3. At -0.4: no extra efficiency penalty (removed from product) → same acceleration
4. Expected: -0.4 should be SLIGHTLY faster. But test shows -0.83s slower.

**The remaining explanation**: The sensitivity test at -0.4 must be affected by something else — possibly the bottoming check at high speed, or the `sus_eff` computation affecting something even though it's not in the product. Or simulation noise from trajectory differences.

### Root Cause 3: Need a Downforce-Drag Tradeoff

Without drag from ride height, there's no reason NOT to go as low as possible (until bottoming). Adding ride height drag creates a real decision:
- Lower = more downforce (faster corners) + more drag (slower straights)
- Higher = less downforce (slower corners) + less drag (faster straights)
- Optimal = track-dependent balance

### Remediation Path A: Add Ride Height Drag

Modify `compute_drag` in `chassis_physics.py` to include ride height:

```python
def compute_drag(speed_kmh, cd, cooling_effort, ride_height=0.0):
    speed_ms = speed_kmh / 3.6
    cooling_drag = 1.0 + cooling_effort * 0.20
    # Lower ride height = more aggressive floor seal = more drag
    rh_drag = 1.0 + max(0, -0.3 - ride_height) * 0.15  # 0% at -0.3, +7.5% at -0.8
    return 0.5 * AIR_DENSITY * cd * REFERENCE_AREA * speed_ms**2 * cooling_drag * rh_drag
```

At rh=-0.3: rh_drag = 1.0 (baseline)
At rh=-0.5: rh_drag = 1.0 + 0.2 × 0.15 = 1.03 (+3% drag)
At rh=-0.8: rh_drag = 1.0 + 0.5 × 0.15 = 1.075 (+7.5% drag)

**This creates the tradeoff**: lower ride height gains ~3% downforce but costs ~3% drag. The net effect depends on the corner/straight ratio of the track.

### Remediation Path B: Remove Baseline Comparison from Grip Factor

Instead of comparing to baseline downforce, use absolute downforce effect:

```python
def compute_grip_factor(tire_mu, downforce, mass_kg, speed_kmh):
    weight = mass_kg * 9.81
    # Effective mu including downforce contribution
    effective_mu = tire_mu * (weight + downforce) / weight
    # Compare against speed profile's assumed mu (4.0)
    profile_mu = 4.0
    return min(1.3, effective_mu / profile_mu)
```

But we already tried this and the grip_factor values at low speed (where downforce is tiny) were 0.3-0.4, making corners impossibly slow.

**Verdict**: Path B was already tried and failed. The speed-profile mu=4.0 assumption is incompatible with speed-dependent downforce.

### Remediation Path C: Drag + Stronger Ground Effect

Combine ride height drag (Path A) with a stronger downforce benefit:
1. Add ride height drag to make low ride height costly on straights
2. Increase the ground_mult range from ×0.3 to ×0.5 so downforce differences are larger
3. Keep the baseline comparison in grip_factor but make it more sensitive

```python
# chassis_physics.py:
ground_mult = 1.0 + (-ride_height) * 0.5  # Was 0.3, now 0.5
# Clamped to [0.5, 1.5]
```

At rh=-0.3: ground_mult = 1.15 (was 1.09)
At rh=-0.5: ground_mult = 1.25 (was 1.15)
Difference: 8.7% (was 5.5%)

With the df_ratio:
- At 200 km/h: (7800+4000)/(7800+3700) = 11800/11500 = 1.026 (was 1.015)

Still only 2.6%. The weight-dominance problem persists.

### Remediation Path D: Downforce Directly Modifies Corner Speed (Not Through Ratio)

Instead of comparing downforce ratios, have downforce directly modify the achievable corner speed through a physics-correct formula:

The speed profile computes `v = sqrt(mu * g * R)` with constant mu=4.0. The actual available grip in a corner is `mu_eff = tire_mu * (weight + downforce) / weight`. The grip_factor should be `mu_eff / profile_mu` — but this is what we already have.

The issue is that `profile_mu = 4.0` already INCLUDES the assumption of speed-dependent downforce. At 200 km/h, the profile assumes a certain downforce level. The grip_factor corrects for the ACTUAL downforce vs the assumed. But the assumed downforce is implicit in the constant mu=4.0, not explicit.

**The real fix**: Make the speed profile's mu speed-dependent AND then compare against the car's actual speed-dependent mu. But this requires restructuring the speed profile computation.

### Recommended: Path A (ride height drag) + Stronger Ground Effect Multiplier

The simplest approach that creates real sensitivity:
1. Add ride height drag: `rh_drag = 1.0 + max(0, -0.3 - ride_height) * 0.15`
2. Increase ground_mult coefficient: `1.0 + (-ride_height) * 0.5` (from 0.3)
3. Pass ride_height to compute_drag call in efficiency_engine.py

This creates a measurable tradeoff:
- Default (-0.3): baseline drag, baseline downforce
- Lower (-0.5): +3% drag, +8.7% downforce → net depends on corner/straight ratio
- Optimized code adapts ride height per-speed to maximize the tradeoff

---

## Execution Plan

### Step 1: Fix differential traction model (one change, measure)
Replace linear traction formula with speed-dependent optimal in `hybrid_physics.py`.
Expected: differential sensitivity goes from -0.53s to +0.3-0.5s.

### Step 2: Fix suspension drag model (one change, measure)
Add ride height drag to `chassis_physics.py` `compute_drag`. Pass ride_height from efficiency_engine.
Expected: creates a downforce-drag tradeoff. Default (-0.3) is no longer tautologically optimal.

### Step 3: Increase ground effect coefficient (one change, measure)
Raise ground_mult from 0.3 to 0.5 in `chassis_physics.py` `compute_downforce`.
Expected: downforce differences become larger, making ride height choice more impactful.

### Step 4: Redesign optimized variants
Write optimized_suspension and optimized_differential that exploit the new physics.
Expected: both show positive sensitivity in the 0.3-0.5s range.

### Step 5: Run both gates, document final distribution
Save results. Update v3.1 proposal with final numbers. Close Phase 1.

**Discipline**: One change per step. Measure after each. No multi-change iterations.
