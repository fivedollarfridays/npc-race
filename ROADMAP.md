# NPC Race Roadmap

> From "optimization puzzle" to "racing game"

## Completed

| Sprint | Name | Cx | Highlights |
|--------|------|----|------------|
| 1 | NPC Race v1.0 | 400 | Tracks, engine, security (bot_scanner + sandbox), CLI |
| 2 | Realistic Racing Viewer | 405 | Layered canvas, car renderer, broadcast overlay, sound, cameras |
| 3 | Tier 1 Realism | 385 | Tire compounds, fuel model, pit lane, lateral movement |
| 4 | Adaptive Intelligence | — | Tournament mode, cross-race learning, reactive cars |
| 5 | Tier 2 Realism | 135 | Tire temperature, DRS, car setup sliders |
| 6 | Realism & Timing | 140 | Physics recalibration, timing module, realistic lap times |
| 7 | Gran Turismo Realism | 135 | Dirty air, downforce, quadratic tire curves, TUMFTM calibration |
| 8 | Pit Wall Dashboard | 155 | 4-zone grid, timing tower, telemetry panels, diagnostics |
| 9 | Collision + Safety Car | 160 | Contact detection, damage model, spin/lockup, safety car |

**Current state:** 1376 tests, 20 tracks, 5 seed cars, simulation.py at 389/395 lines.

## Up Next

| Sprint | Name | What It Adds | Strategic Impact |
|--------|------|-------------|------------------|
| **10** | **Weather System** | Dry/wet transitions, intermediates, full wets, forecasts | Wrong tire = 30s lost. Right call = 5 positions. |
| **11** | **ERS + Brake Temp** | Battery deploy/harvest, brake heat/fade | More decisions per lap on three axes. |
| **12** | **Information Asymmetry** | Hidden opponent data, inference from lap times | Strategy under uncertainty. |
| **13** | **Narrative Engine** | Battle detection, auto-commentary, race reports | The race tells a story. |
| **14** | **Sound Overhaul** | Spatial audio, per-car engine, crowd | Close your eyes and know it's a race. |
| **15** | **Viewer Polish** | TV Director camera, broadcast labels | Looks like a real broadcast. |
| **16** | **Championship Mode** | Multi-race season, points, car development | Win the season, not just the race. |

## Sprint Details

Full technical designs for each sprint are in [`docs/roadmap-sprints-9-16.md`](docs/roadmap-sprints-9-16.md).

### Sprint 10: Weather System

**Core mechanic:** Track wetness 0.0 (bone dry) to 1.0 (standing water). Weather transitions are probabilistic. Forecasts available to strategies but can be wrong.

**New compounds:** intermediate (optimal 0.3-0.6 wetness), full wet (optimal 0.6-1.0).

**Strategy fields:** `track_wetness`, `weather_forecast`, expanded `tire_compound`.

### Sprint 11: ERS + Brake Temp

**ERS:** 0-4 MJ battery. Deploy for attack boost, harvest under braking. Strategy chooses deploy mode.

**Brakes:** Temperature model like tires. Hot brakes fade, affecting corner entry speed.

### Sprint 12: Information Asymmetry

Your car: full data. Opponents: position, speed, gap, compound, tire age only. Smart agents infer opponent state from observable behavior.

### Sprint 13-16

Narrative engine (auto-commentary), sound overhaul (spatial audio), viewer polish (TV Director), championship mode (multi-race season with car development).

## Release Milestones

- **v1.0** — PyPI publish (plan exists: `plan-2026-03-npc-race-get-sellable`)
- **v2.0** — After Weather + ERS (Sprints 10-11), full F1 strategy depth
- **v3.0** — After Championship Mode (Sprint 16), complete game loop
