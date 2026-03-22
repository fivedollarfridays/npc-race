# NPC Race — Sensitivity Test
Date: 2026-03-21 23:25
Track: Monza | Laps: 1 | Seed: 42 | Car: BrickHouse (idx 0)

## Baseline: 80.83s

## Per-Part Sensitivity

| Part                 |    Default |  Optimized |       Gain |   Note |
|----------------------|------------|------------|------------|--------|
| engine_map           |      80.83 |      80.83 |     +0.000s |        |
| gearbox              |      80.83 |      79.63 |     +1.200s |    *** |
| ers_deploy           |      80.83 |      80.50 |     +0.333s |        |
| ers_harvest          |      80.83 |      80.83 |     +0.000s |        |
| brake_bias           |      80.83 |      80.83 |     +0.000s |        |
| suspension           |      80.83 |      81.67 |     -0.833s |    BAD |
| cooling              |      80.83 |      80.27 |     +0.567s |    *** |
| fuel_mix             |      80.83 |      80.33 |     +0.500s |        |
| differential         |      80.83 |      81.37 |     -0.533s |    BAD |

| ALL OPTIMIZED        |      80.83 |      77.37 |     +3.467s |        |
| SUM OF PARTS         |            |            |     +1.233s |        |
| INTERACTION          |            |            |     +2.233s |        |

## Dominance Check

- engine_map: 0% of total
- gearbox: 35% of total **DOMINANT**
- ers_deploy: 10% of total
- ers_harvest: 0% of total
- brake_bias: 0% of total
- suspension: -24% of total
- cooling: 16% of total
- fuel_mix: 14% of total
- differential: -15% of total

## Interaction Pairs

| Pair                           |    A alone |    B alone |        A+B |   Expected |  Interaction |
|--------------------------------|------------|------------|------------|------------|--------------|
| engine_map + gearbox           |     +0.000 |     +1.200 |     +1.200 |     +1.200 |       +0.000 |
| brake_bias + ers_harvest       |     +0.000 |     +0.000 |     +0.000 |     +0.000 |       +0.000 |
| suspension + cooling           |     -0.833 |     +0.567 |     +0.200 |     -0.267 |       +0.467 |
| ers_deploy + differential      |     +0.333 |     -0.533 |     +0.167 |     -0.200 |       +0.367 |
| engine_map + fuel_mix          |     +0.000 |     +0.500 |     +0.500 |     +0.500 |       +0.000 |

## Summary

- **Baseline:** 80.83s
- **All optimized:** 77.37s
- **Total spread:** 3.47s (target: 3.0-5.0s)
- **Parts with > 0.3s gain:** 4/9
- **Parts with negative gain (worse):** 2/9
- **Coupled pairs (interaction > 0.03s):** 2/5

## Gate Criteria (1-lap)

- [x] 3-5s spread: 3.47s
- [ ] ≥5 parts above 0.3s: 4/9
- [x] No part above 1.2s
- [x] No part > 35% of total
- [ ] ≥3 coupled pairs

**GATE: FAIL**

---

# 5-Lap Race Verification

## Baseline (5 laps): 402.10s

| Part | Default | Optimized | Gain |
|------|---------|-----------|------|
| engine_map      | 402.10 | 402.10 | +0.00s |
| brake_bias      | 402.10 | 402.10 | +0.00s |
| ers_deploy      | 402.10 | 401.50 | +0.60s |
| ers_harvest     | 402.10 | 401.33 | +0.77s |
| ALL OPTIMIZED   | 402.10 | 382.60 | +19.50s |

## Gate Criteria (5-lap)

- [x] Total spread ≥ 10s: 19.50s
- [x] ≥2 multi-lap parts above 0.3s
  - engine_map: +0.00s —
  - brake_bias: +0.00s —
  - ers_deploy: +0.60s ✓
  - ers_harvest: +0.77s ✓

**5-LAP GATE: PASS**

**COMBINED GATE: FAIL**