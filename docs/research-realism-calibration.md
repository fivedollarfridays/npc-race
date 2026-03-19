# Realism & Calibration Research — Sprint 7 Planning

> Compiled 2026-03-17. Sources: TUMFTM/race-simulation, Fast-F1, Speed Dreams, f1metrics, FormulaGPT, iRacing docs.

## Real F1 Calibration Targets

### Track Data (2024 Season)

| Track | Race Fastest Lap | Top Speed | Min Corner | Fuel/Lap |
|-------|-----------------|-----------|------------|----------|
| Monza | 81.4s | 357 km/h | 72-89 km/h | ~3.0 kg |
| Monaco | 74.2s | 290-295 km/h | 45 km/h | ~2.2 kg |
| Silverstone | 88.3s | 327 km/h | 85-90 km/h | ~2.6 kg |

### Tire Data

| Compound | Stint Life | Deg Rate (s/lap) | Fresh Pace Delta |
|----------|-----------|-----------------|------------------|
| Soft | 10-20 laps | 0.08-0.15 | baseline |
| Medium | 25-40 laps | 0.05-0.10 | +0.5-0.8 s/lap |
| Hard | 35-60 laps | 0.03-0.06 | +0.9-1.5 s/lap |

- Tire temp surface: 100-120°C optimal (up to 150°C peak)
- Degradation curve: warm-up (laps 1-3) → linear → cliff
- Fuel-corrected degradation adds ~0.03 s/lap (fuel burn masks true deg)

### Pit Stop

- Stationary: 2.0-2.5s (top teams)
- Total time loss: 20-25s
- Speed limit: 80 km/h (60 km/h Monaco)

### Fuel

- Fuel effect on lap time: 0.03-0.04 s/kg/lap (TUMFTM: 0.027)
- TUMFTM Monza consumption: 1.981 kg/lap
- Starting fuel: ~105 kg
- Max fuel load: 110 kg (regulation)

## Gap Analysis: NPC Race vs Reality

| System | NPC Race Now | Real F1 | Gap | Priority |
|--------|-------------|---------|-----|----------|
| **Dirty air** | Not modeled | 0.95x grip when following in corners | **MISSING** | CRITICAL |
| **Speed-dependent downforce** | Not modeled | Grip ∝ v² | **MISSING** | HIGH |
| **Pre-cliff degradation** | Linear (1 - wear*0.3) | Quadratic (convex curve) | Wrong shape | HIGH |
| **Fuel consumption** | 1.62 kg/lap | ~2.0-3.0 kg/lap | 20-50% low | MEDIUM |
| **Temp-grip curve** | Piecewise linear | Quadratic parabola | Shape wrong | MEDIUM |
| **Compound pace delta** | base_grip (1.15/1.00/0.85) | ~0.5-0.8 s/lap between steps | Needs validation | MEDIUM |
| **Pit stop total** | 26s | 20-25s | Slightly high | LOW |
| **DRS benefit** | 5% speed | 10-15 km/h (~3-4%) | Close enough | LOW |
| **ERS/deployment** | Not modeled | 120kW, 33s/lap deploy | **MISSING** | FUTURE |
| **Safety car** | Not modeled | Randomizes strategy | **MISSING** | FUTURE |
| **Weather** | Not modeled | Transforms strategy | **MISSING** | FUTURE |

## Key Formulas to Adopt

### From Speed Dreams: Quadratic temp-grip

```python
grip_factor = max(0.5, 1.0 - k * (T - T_optimal)**2)
# Where k = 0.5 / (T_optimal - T_ambient)**2
```

### From f1metrics: Dirty air

```python
if gap_ahead_s < 1.5 and curvature > 0.01:
    grip_mult *= 0.95 - 0.03 * (1.0 - gap_ahead_s / 1.5)
    # At 0s gap: 0.92x grip. At 1.5s gap: 0.95x. Beyond 1.5s: no effect.
    tire_wear_mult *= 1.10  # 10% faster wear in dirty air
```

### Speed-dependent aero grip

```python
aero_grip_bonus = aero_stat * (speed / 300)**2 * DOWNFORCE_GRIP_FACTOR
effective_grip = base_grip + aero_grip_bonus
```

### Quadratic pre-cliff degradation

```python
# Before: grip = base_grip * (1.0 - wear * 0.3)
# After:  grip = base_grip * (1.0 - wear**1.5 * 0.3)
```

## What "Gran Turismo Level" Means for a Strategy Sim

GT7 is a *driving* sim — physics serve haptic/visual feedback.
NPC Race is a *strategy* sim — physics must create realistic **decision space**.

### Must Have (creates strategy)

- Non-linear tire degradation with cliff ✓
- Compound differentiation ✓
- Fuel weight effect ✓
- Pit stop time cost ✓
- **Dirty air (corner grip penalty)** ← MISSING
- **Speed-dependent downforce** ← MISSING
- Track-dependent character ✓
- Driving mode tradeoff ✓

### Should Have (adds depth)

- Quadratic pre-cliff degradation
- Dirty-air tire wear multiplier
- Friction-power-based tire heat
- Safety car / VSC randomization

### Don't Need (visual/haptic only)

- Per-wheel slip angles / Pacejka
- Suspension geometry
- Contact patch slicing
- Brake temperature
- Engine torque curves / gear ratios

## Source References

- [TUMFTM/race-simulation](https://github.com/TUMFTM/race-simulation) — academic F1 sim, 88 track/year parameter files
- [Fast-F1](https://github.com/theOehrly/Fast-F1) — real telemetry data via F1 API
- [Speed Dreams](http://www.speed-dreams.org/) — friction-power tire model
- [f1metrics race simulator](https://f1metrics.wordpress.com/2014/10/03/building-a-race-simulator/)
- [FormulaGPT](https://github.com/dawid-maj/FormulaGPT) — LLM racing agents pattern
- [iRacing NTM V7](https://www.iracing.com/physics-modeling-ntm-v7-info-plus/) — full sim reference
