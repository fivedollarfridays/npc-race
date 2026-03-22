# NPC Race — Sensitivity Test
Date: 2026-03-22 11:55
Track: Monza | Laps: 1 | Seed: 42 | Car: BrickHouse (idx 0)

## Baseline: 81.13s

## Per-Part Sensitivity

| Part                 |    Default |  Optimized |       Gain |   Note |
|----------------------|------------|------------|------------|--------|
| engine_map           |      81.13 |      81.13 |     +0.000s |        |
| gearbox              |      81.13 |      79.73 |     +1.400s |    *** |
| ers_deploy           |      81.13 |      80.33 |     +0.800s |    *** |
| ers_harvest          |      81.13 |      81.13 |     +0.000s |        |
| brake_bias           |      81.13 |      81.13 |     +0.000s |        |
| suspension           |      81.13 |      80.13 |     +1.000s |    *** |
| cooling              |      81.13 |      80.27 |     +0.867s |    *** |
| fuel_mix             |      81.13 |      80.40 |     +0.733s |    *** |
| differential         |      81.13 |      80.77 |     +0.367s |        |

| ALL OPTIMIZED        |      81.13 |      75.33 |     +5.800s |        |
| SUM OF PARTS         |            |            |     +5.167s |        |
| INTERACTION          |            |            |     +0.633s |        |

## Dominance Check

- engine_map: 0% of total
- gearbox: 24% of total
- ers_deploy: 14% of total
- ers_harvest: 0% of total
- brake_bias: 0% of total
- suspension: 17% of total
- cooling: 15% of total
- fuel_mix: 13% of total
- differential: 6% of total

## Interaction Pairs

| Pair                           |    A alone |    B alone |        A+B |   Expected |  Interaction |
|--------------------------------|------------|------------|------------|------------|--------------|
| engine_map + gearbox           |     +0.000 |     +1.400 |     +1.400 |     +1.400 |       +0.000 |
| brake_bias + ers_harvest       |     +0.000 |     +0.000 |     +0.000 |     +0.000 |       +0.000 |
| suspension + cooling           |     +1.000 |     +0.867 |     +1.067 |     +1.867 |       -0.800 |
| ers_deploy + differential      |     +0.800 |     +0.367 |     +2.367 |     +1.167 |       +1.200 |
| engine_map + fuel_mix          |     +0.000 |     +0.733 |     +0.733 |     +0.733 |       +0.000 |

## Summary

- **Baseline:** 81.13s
- **All optimized:** 75.33s
- **Total spread:** 5.80s (target: 3.0-5.0s)
- **Parts with > 0.3s gain:** 6/9
- **Parts with negative gain (worse):** 0/9
- **Coupled pairs (interaction > 0.03s):** 2/5

## Gate Criteria (1-lap)

- [ ] 3-5s spread: 5.80s
- [x] ≥4 parts above 0.3s: 6/9
- [ ] No part above 1.2s
- [x] No part > 35% of total
- [ ] ≥3 coupled pairs

**GATE: FAIL**

---

# 5-Lap Race Verification

## Baseline (5 laps): 393.77s

| Part | Default | Optimized | Gain |
|------|---------|-----------|------|
| engine_map      | 393.77 | 393.77 | +0.00s |
| brake_bias      | 393.77 | 393.77 | +0.00s |
| ers_deploy      | 393.77 | 393.10 | +0.67s |
| ers_harvest     | 393.77 | 393.37 | +0.40s |
| ALL OPTIMIZED   | 393.77 | 376.00 | +17.77s |

## Gate Criteria (5-lap)

- [x] Total spread ≥ 15s: 17.77s
- [x] ≥2 multi-lap parts above 0.3s
  - engine_map: +0.00s —
  - brake_bias: +0.00s —
  - ers_deploy: +0.67s ✓
  - ers_harvest: +0.40s ✓

**5-LAP GATE: PASS**

**COMBINED GATE: FAIL**