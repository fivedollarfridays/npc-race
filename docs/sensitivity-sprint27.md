# NPC Race — Sensitivity Test
Date: 2026-03-22 00:12
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
| suspension           |      80.83 |      81.87 |     -1.033s |    BAD |
| cooling              |      80.83 |      80.27 |     +0.567s |    *** |
| fuel_mix             |      80.83 |      80.33 |     +0.500s |        |
| differential         |      80.83 |      82.20 |     -1.367s |    BAD |

| ALL OPTIMIZED        |      80.83 |      77.83 |     +3.000s |        |
| SUM OF PARTS         |            |            |     +0.200s |        |
| INTERACTION          |            |            |     +2.800s |        |

## Dominance Check

- engine_map: 0% of total
- gearbox: 40% of total **DOMINANT**
- ers_deploy: 11% of total
- ers_harvest: 0% of total
- brake_bias: 0% of total
- suspension: -34% of total **DOMINANT**
- cooling: 19% of total
- fuel_mix: 17% of total
- differential: -46% of total **DOMINANT**

## Interaction Pairs

| Pair                           |    A alone |    B alone |        A+B |   Expected |  Interaction |
|--------------------------------|------------|------------|------------|------------|--------------|
| engine_map + gearbox           |     +0.000 |     +1.200 |     +1.200 |     +1.200 |       +0.000 |
| brake_bias + ers_harvest       |     +0.000 |     +0.000 |     +0.000 |     +0.000 |       +0.000 |
| suspension + cooling           |     -1.033 |     +0.567 |     -0.833 |     -0.467 |       -0.367 |
| ers_deploy + differential      |     +0.333 |     -1.367 |     +0.767 |     -1.033 |       +1.800 |
| engine_map + fuel_mix          |     +0.000 |     +0.500 |     +0.500 |     +0.500 |       +0.000 |

## Summary

- **Baseline:** 80.83s
- **All optimized:** 77.83s
- **Total spread:** 3.00s (target: 3.0-5.0s)
- **Parts with > 0.3s gain:** 4/9
- **Parts with negative gain (worse):** 2/9
- **Coupled pairs (interaction > 0.03s):** 2/5

## Gate Criteria (1-lap)

- [x] 3-5s spread: 3.00s
- [x] ≥4 parts above 0.3s: 4/9
- [x] No part above 1.2s
- [ ] No part > 35% of total
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
| ALL OPTIMIZED   | 402.10 | 385.43 | +16.67s |

## Gate Criteria (5-lap)

- [x] Total spread ≥ 15s: 16.67s
- [x] ≥2 multi-lap parts above 0.3s
  - engine_map: +0.00s —
  - brake_bias: +0.00s —
  - ers_deploy: +0.60s ✓
  - ers_harvest: +0.77s ✓

**5-LAP GATE: PASS**

**COMBINED GATE: FAIL**