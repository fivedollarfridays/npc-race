# NPC Race — Sensitivity Test (SUPERSEDED by sensitivity-sprint26.md)
# This result used 50x-wrong lateral G formula.
Date: 2026-03-21 12:41
Track: Monza | Laps: 1 | Seed: 42 | Car: BrickHouse (idx 0)

## Baseline: 86.43s

## Per-Part Sensitivity

| Part                 |    Default |  Optimized |       Gain |   Note |
|----------------------|------------|------------|------------|--------|
| engine_map           |      86.43 |      86.43 |     +0.000s |        |
| gearbox              |      86.43 |      85.50 |     +0.933s |    *** |
| ers_deploy           |      86.43 |      85.63 |     +0.800s |    *** |
| ers_harvest          |      86.43 |      86.40 |     +0.033s |        |
| brake_bias           |      86.43 |      86.40 |     +0.033s |        |
| suspension           |      86.43 |      85.63 |     +0.800s |    *** |
| cooling              |      86.43 |      85.60 |     +0.833s |    *** |
| fuel_mix             |      86.43 |      85.43 |     +1.000s |    *** |
| differential         |      86.43 |      85.63 |     +0.800s |    *** |

| ALL OPTIMIZED        |      86.43 |      82.40 |     +4.033s |        |
| SUM OF PARTS         |            |            |     +5.233s |        |
| INTERACTION          |            |            |     -1.200s |        |

## Dominance Check

- engine_map: 0% of total
- gearbox: 23% of total
- ers_deploy: 20% of total
- ers_harvest: 1% of total
- brake_bias: 1% of total
- suspension: 20% of total
- cooling: 21% of total
- fuel_mix: 25% of total
- differential: 20% of total

## Interaction Pairs

| Pair                           |    A alone |    B alone |        A+B |   Expected |  Interaction |
|--------------------------------|------------|------------|------------|------------|--------------|
| engine_map + gearbox           |     +0.000 |     +0.933 |     +0.933 |     +0.933 |       +0.000 |
| brake_bias + ers_harvest       |     +0.033 |     +0.033 |     +0.100 |     +0.067 |       +0.033 |
| suspension + cooling           |     +0.800 |     +0.833 |     +1.400 |     +1.633 |       -0.233 |
| ers_deploy + differential      |     +0.800 |     +0.800 |     +2.000 |     +1.600 |       +0.400 |
| engine_map + fuel_mix          |     +0.000 |     +1.000 |     +1.000 |     +1.000 |       +0.000 |

## Summary

- **Baseline:** 86.43s
- **All optimized:** 82.40s
- **Total spread:** 4.03s (target: 3.0-5.0s)
- **Parts with > 0.3s gain:** 6/9
- **Parts with negative gain (worse):** 0/9
- **Coupled pairs (interaction > 0.03s):** 3/5

## Gate Criteria (1-lap)

- [x] 3-5s spread: 4.03s
- [x] ≥5 parts above 0.3s: 6/9
- [x] No part above 1.2s
- [x] No part > 35% of total
- [x] ≥3 coupled pairs

**GATE: PASS**

---

# 5-Lap Race Verification

## Baseline (5 laps): 418.30s

| Part | Default | Optimized | Gain |
|------|---------|-----------|------|
| engine_map      | 418.30 | 418.30 | +0.00s |
| brake_bias      | 418.30 | 418.27 | +0.03s |
| ers_deploy      | 418.30 | 418.87 | -0.57s |
| ers_harvest     | 418.30 | 418.33 | -0.03s |
| ALL OPTIMIZED   | 418.30 | 408.30 | +10.00s |

## Gate Criteria (5-lap)

- [x] Total spread ≥ 10s: 10.00s
- [ ] ≥2 multi-lap parts above 0.3s
  - engine_map: +0.00s —
  - brake_bias: +0.03s —
  - ers_deploy: -0.57s —
  - ers_harvest: -0.03s —

**5-LAP GATE: FAIL**

**COMBINED GATE: FAIL**