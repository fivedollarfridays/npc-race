# Current State

> Last updated: 2026-03-17 T3.10 done — Sprint 3 realism overhaul complete

## Active Plan

**Plan:** plan-2026-03-npc-race-realism — Tier 1 Realism Foundation
**Status:** Complete (10 tasks, 5 waves)
**Total Complexity:** 385 Cx

## Current Focus

Sprint 3 complete. 772 tests passing. Realistic lap times, tire compounds, fuel, pit stops, lateral movement all working. Ready for review/ship.

## Completed Sprints

### Sprint 1 — NPC Race v1.0 (11 tasks, 400 Cx) ✓

Tracks package (20 presets), engine decomposition, security (bot_scanner + sandbox), CLI packaging, viewer track name, balance testing, integration tests. All done.

### Sprint 2 — Realistic Racing Viewer (11 tasks, 405 Cx) ✓

Replay enrichment, build system, layered canvas, track renderer (kerbs, grass, asphalt), car renderer (top-down with wheels), F1 broadcast overlay, sound engine, physics effects, camera system (full/follow/onboard), integration polish. All done.

### Sprint 3 — Tier 1 Realism Foundation (10 tasks, 385 Cx) ✓

| ID | Task | Status |
|----|------|--------|
| T3.1 | Track real-world data (real_length_m, real_laps) | done |
| T3.2 | Tire compound model (soft/medium/hard, cliff) | done |
| T3.3 | Fuel load model (consumption, weight, engine modes) | done |
| T3.4 | Lateral movement system | done |
| T3.5 | Pit lane state machine | done |
| T3.6 | Simulation integration (wire all systems) | done |
| T3.7 | Strategy interface + sandbox update | done |
| T3.8 | Seed car rewrite (5 cars with pit/fuel/lateral) | done |
| T3.9 | Replay enrichment (compounds, fuel, pit status) | done |
| T3.10 | Balance testing + integration gate | done |

## Key Metrics

- **772 tests**, all passing
- **Monaco lap: ~58-65s** (target 60-90s)
- **Monza lap: ~65s** (target 65-95s)
- **Balance: Silky 3 wins, GlassCanon 3 wins** (50/50 across 6 tracks)
- **Pit stops working**: BrickHouse 2-stop, GooseLoose/Silky/SlipStream 1-stop, GlassCanon 0-stop

## What's Next

1. Review, fix, simplify, commit, PR
2. Tier 2 realism: tire temperature, DRS zones, expanded car setup

## Blockers

None.

## Notes

- Trello not connected (trello.enabled: false)
- No external dependencies — Python stdlib only
- simulation.py: 335 lines / 14 functions (limits: 400/15)
- Archived full session history: `.paircoder/archive/state-pre-cleanup-2026-03-17.md`
