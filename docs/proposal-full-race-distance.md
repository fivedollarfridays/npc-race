# Proposal: Full Race Distance, Qualifying, and Player UX

> Status: Approved | Date: 2026-03-23

## Problem Statement

NPC Race simulates F1 physics at 30Hz tick-by-tick fidelity. This works
for 5-lap demos but breaks at real F1 distances:

| Scenario | Laps | Cars | Wall Time | Replay Size |
|----------|------|------|-----------|-------------|
| Current default | 5 | 6 | 35s | 113 MB |
| Full Monza | 53 | 20 | ~20 min | 3.4 GB |
| Full Monaco | 78 | 20 | ~30 min | 5+ GB |

## Decisions (Approved)

| Question | Decision |
|----------|----------|
| Tick rate | 30Hz always, both modes |
| Qualifying | Single flying lap |
| Rivals | Templates with noise (4 archetypes) |
| Full-race viewer | Race summary dashboard, not replay interpolation |
| Race weekend | `npcrace race --qualify` pipeline |
| A/B testing | Skip (already works) |

## Execution: Sprint 34 + 35

### Sprint 34: Fast Sim + Qualifying (29 Cx)
- Sparse storage (1fps frames, lap_summary.json)
- Sim performance (spatial indexing, strategy throttle, track precompute)
- Qualifying (flying lap, grid.json, race pipeline)

### Sprint 35: Full Grid + Real Distances (21 Cx)
- 14 rival cars from archetype templates
- Real F1 lap counts on all 20 tracks
- Race summary dashboard (terminal)

## Constraints
- 30Hz physics always. Fast mode only changes storage + strategy call frequency.
- No breaking changes to car files or part function signatures.
- Tick rate validation (10Hz) is a separate future effort.
