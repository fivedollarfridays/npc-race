# NPC Race — Sensitivity Test
Date: 2026-03-21 01:34
Track: Monza | Laps: 1 | Seed: 42 | Car: BrickHouse (idx 0)

## Baseline: 87.73s

## Per-Part Sensitivity

| Part                 |    Default |  Optimized |       Gain |   Note |
|----------------------|------------|------------|------------|--------|
| engine_map           |      87.73 |      87.73 |     +0.000s |        |
| gearbox              |      87.73 |      87.70 |     +0.033s |        |
| ers_deploy           |      87.73 |      87.40 |     +0.333s |        |
| ers_harvest          |      87.73 |      87.73 |     +0.000s |        |
| brake_bias           |      87.73 |      87.73 |     +0.000s |        |
| suspension           |      87.73 |      88.30 |     -0.567s |    BAD |
| cooling              |      87.73 |      87.80 |     -0.067s |        |
| fuel_mix             |      87.73 |      87.80 |     -0.067s |        |
| differential         |      87.73 |      87.77 |     -0.033s |        |

| ALL OPTIMIZED        |      87.73 |      87.80 |     -0.067s |        |
| SUM OF PARTS         |            |            |     -0.367s |        |
| INTERACTION          |            |            |     +0.300s |        |

## Dominance Check

- engine_map: -0% of total
- gearbox: -50% of total **DOMINANT**
- ers_deploy: -500% of total **DOMINANT**
- ers_harvest: -0% of total
- brake_bias: -0% of total
- suspension: 850% of total **DOMINANT**
- cooling: 100% of total **DOMINANT**
- fuel_mix: 100% of total **DOMINANT**
- differential: 50% of total **DOMINANT**

## Interaction Pairs

| Pair                           |    A alone |    B alone |        A+B |   Expected |  Interaction |
|--------------------------------|------------|------------|------------|------------|--------------|
| engine_map + gearbox           |     +0.000 |     +0.033 |     +0.033 |     +0.033 |       +0.000 |
| brake_bias + ers_harvest       |     +0.000 |     +0.000 |     +0.000 |     +0.000 |       +0.000 |
| suspension + cooling           |     -0.567 |     -0.067 |     -0.633 |     -0.633 |       +0.000 |
| ers_deploy + differential      |     +0.333 |     -0.033 |     +0.367 |     +0.300 |       +0.067 |
| engine_map + fuel_mix          |     +0.000 |     -0.067 |     -0.067 |     -0.067 |       +0.000 |

## Summary

- **Baseline:** 87.73s
- **All optimized:** 87.80s
- **Total spread:** -0.07s (target: 10.0s)
- **Parts with > 0.5s gain:** 0/9
- **Parts with negative gain (worse):** 1/9
- **Coupled pairs (interaction > 0.05s):** 1/5

## Gate Criteria

- [ ] 10s spread: -0.07s
- [ ] ≥5 parts in 0.5-1.5s range
- [ ] No part > 25% of total
- [ ] ≥3 coupled pairs

**GATE: FAIL**