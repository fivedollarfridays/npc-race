# NPC Race — Sensitivity Test
Date: 2026-03-21 02:41
Track: Monza | Laps: 1 | Seed: 42 | Car: BrickHouse (idx 0)

## Baseline: 120.80s

## Per-Part Sensitivity

| Part                 |    Default |  Optimized |       Gain |   Note |
|----------------------|------------|------------|------------|--------|
| engine_map           |     120.80 |     119.20 |     +1.600s |    *** |
| gearbox              |     120.80 |     119.40 |     +1.400s |    *** |
| ers_deploy           |     120.80 |     119.67 |     +1.133s |    *** |
| ers_harvest          |     120.80 |     120.87 |     -0.067s |        |
| brake_bias           |     120.80 |     118.97 |     +1.833s |    *** |
| suspension           |     120.80 |     118.57 |     +2.233s |    *** |
| cooling              |     120.80 |     120.80 |     +0.000s |        |
| fuel_mix             |     120.80 |     120.80 |     +0.000s |        |
| differential         |     120.80 |     118.83 |     +1.967s |    *** |

| ALL OPTIMIZED        |     120.80 |     110.03 |    +10.767s |        |
| SUM OF PARTS         |            |            |    +10.100s |        |
| INTERACTION          |            |            |     +0.667s |        |

## Dominance Check

- engine_map: 15% of total
- gearbox: 13% of total
- ers_deploy: 11% of total
- ers_harvest: -1% of total
- brake_bias: 17% of total
- suspension: 21% of total
- cooling: 0% of total
- fuel_mix: 0% of total
- differential: 18% of total

## Interaction Pairs

| Pair                           |    A alone |    B alone |        A+B |   Expected |  Interaction |
|--------------------------------|------------|------------|------------|------------|--------------|
| engine_map + gearbox           |     +1.600 |     +1.400 |     +3.533 |     +3.000 |       +0.533 |
| brake_bias + ers_harvest       |     +1.833 |     -0.067 |     +1.833 |     +1.767 |       +0.067 |
| suspension + cooling           |     +2.233 |     +0.000 |     +2.267 |     +2.233 |       +0.033 |
| ers_deploy + differential      |     +1.133 |     +1.967 |     +3.067 |     +3.100 |       -0.033 |
| engine_map + fuel_mix          |     +1.600 |     +0.000 |     +1.600 |     +1.600 |       +0.000 |

## Summary

- **Baseline:** 120.80s
- **All optimized:** 110.03s
- **Total spread:** 10.77s (target: 10.0s)
- **Parts with > 0.5s gain:** 6/9
- **Parts with negative gain (worse):** 0/9
- **Coupled pairs (interaction > 0.05s):** 4/5

## Gate Criteria

- [x] 10s spread: 10.77s
- [x] ≥5 parts in 0.5-2.0s range
- [x] No part > 25% of total
- [x] ≥3 coupled pairs

**GATE: PASS**