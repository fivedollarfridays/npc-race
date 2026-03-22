# Phase 4 Proposal — League System + Viewer Additions

> Date: 2026-03-22 | Status: For Review

## Recommendation: Split Into Two Sprints

**Sprint 30: League System** (gameplay-critical, backend)
**Sprint 31: Viewer Additions** (experience polish, frontend)

The league system defines progression, gates entry, and restricts parts. It changes how the game works. The viewer additions (live code terminal, TRON diagnostic) make watching races better but don't change gameplay. Ship leagues first so F3-to-Championship flow can be tested with real car projects, then layer viewer polish on top.

---

## Sprint 30 — League System

### What It Does

Players progress through tiers by implementing more parts and writing cleaner code:

| League | Parts | Quality Gate | Target Lap | Entry |
|--------|-------|-------------|-----------|-------|
| **F3** | 3 (gearbox, cooling, strategy) | Must parse, no crashes | ~86-92s | Default — everyone starts here |
| **F2** | 6 (+ suspension, ers_deploy, fuel_mix) | Advisory: ruff clean recommended | ~82-86s | Submit 3 working F3 parts |
| **F1** | All 10 | Enforced: ruff clean required | ~79-82s | Submit 6 working F2 parts |
| **Championship** | All 10 + multi-file | Full quality gate (CC < 15, reliability ≥ 0.88) | ~78-80s | Submit all 10, pass quality |

**Part assignment rationale**: Every part unlocked at a tier produces measurable sensitivity at that tier's race distance. F3 parts (gearbox 1.40s, cooling 0.87s, strategy) all show clear cause-and-effect on 1-lap. F2 adds parts with 0.37-1.00s sensitivity. F1 adds the four multi-lap parts (engine_map, brake_bias, differential, ers_harvest) where full race distance makes them meaningful.

### Advisory vs Enforced Gates

**F3/F2 (advisory)**: Code quality is measured and reported but never blocks entry. A player sees "your code has 3 lint violations — this would cost you 0.5s per lap from glitches at F1 level" but can still race. This teaches quality without frustrating beginners.

**F1/Championship (enforced)**: Ruff must pass. CC limits enforced. Cars that fail quality checks are rejected with specific feedback: "gearbox.py has cyclomatic complexity 18 (limit 15). Simplify the conditional logic."

### Integration Points (Already Built)

| System | What Exists | How League Uses It |
|--------|------------|-------------------|
| `car_project_loader._loaded_parts` | Lists which parts a car implements | Determines tier: 3 parts = F3, 6 = F2, 10 = F1 |
| `code_quality.compute_reliability_score()` | Returns 0.50-1.00 from AST metrics | Advisory report for F3/F2, enforced gate for F1/Championship |
| `code_quality.compute_cyclomatic_complexity()` | CC per function | Enforced CC < 15 for F1+ |
| `code_quality.check_type_hints()` | Fraction of typed functions | Enforced ≥ 80% for Championship |
| `bot_scanner.scan_car_project()` | Security scan | Required for all tiers |
| `glitch.GlitchEngine` | Reliability → glitch rate | Glitches affect all tiers equally (physics consequence of code quality) |

### New Module: `engine/league_system.py`

```python
LEAGUE_TIERS = ["F3", "F2", "F1", "Championship"]

LEAGUE_PARTS = {
    "F3": ["gearbox", "cooling", "strategy"],
    "F2": ["gearbox", "cooling", "suspension", "ers_deploy", "fuel_mix", "strategy"],
    "F1": CAR_PARTS,  # All 10 — adds engine_map, brake_bias, differential, ers_harvest
    "Championship": CAR_PARTS,
}

def determine_league(car: dict) -> str
def validate_car_for_league(car: dict, league: str) -> LeagueResult
def generate_quality_report(car: dict, league: str) -> QualityReport
```

### Tasks

**T30.1 — League definitions + validation** (Cx: 15)
- `engine/league_system.py`: tier definitions, part restrictions, `determine_league()`, `validate_car_for_league()`
- A car with 3 loaded parts auto-slots to F3. A car with 10 + high reliability = Championship.

**T30.2 — Quality gate enforcement** (Cx: 15)
- Advisory reports for F3/F2: show quality cost without blocking
- Enforced gates for F1/Championship: ruff clean + CC limits
- `generate_quality_report()` returns structured feedback

**T30.3 — Wire into race runner** (Cx: 10)
- `race_runner.py`: accept `--league` flag. Validate cars before loading.
- `cli/commands.py`: add league parameter to `cmd_run()`
- Default: auto-detect league from loaded parts

**T30.4 — Integration gate** (Cx: 10)
- F3 car with 3 parts (gearbox, cooling, strategy) races successfully
- F2 car with 6 parts races with advisory quality report
- F1 car failing ruff check is rejected
- Championship car with CC > 15 is rejected with feedback
- Auto-detection: 3 parts → F3, 10 parts → F1

---

## Sprint 31 — Viewer Additions

### What It Adds

1. **Live Code Terminal**: Right panel showing part function calls in real-time as the race runs. Each tick shows which functions were called, their inputs, outputs, and status (ok/glitch/error).

2. **TRON Car Diagnostic**: Wireframe car visualization with parts that pulse when called and flash red on glitch. Shows tire wear, engine temp, ERS charge, fuel level as gauges on the car diagram.

3. **Code Grade Card**: Reliability score display with letter grade (A-D), per-metric breakdown, and glitch counter per lap.

### Prerequisites

**Call logs in replay**: The current replay format doesn't include per-part call data. Sprint 31 needs to add `call_logs` to the replay export (from `PartsRaceSim.call_logs` which already exists but isn't exported).

### Tasks

**T31.1 — Export call logs to replay** (Cx: 10)
- Modify `replay.py` to include per-car part call data
- Trim to essential fields (part name, output, status, glitch info)
- Keep replay file size reasonable (sample every N ticks, not every tick)

**T31.2 — Live code terminal JS** (Cx: 20)
- `viewer/js/code-terminal.js`: render part calls synchronized with replay playback
- Color-coded: green (ok), yellow (clamped), red (glitch/error)
- Scrolling log view that follows the current tick

**T31.3 — TRON car diagnostic JS** (Cx: 20)
- `viewer/js/car-diagnostic.js`: wireframe car with part indicators
- Parts pulse on call, flash on glitch
- Gauges: tire wear, engine temp, ERS, fuel

**T31.4 — Code grade card** (Cx: 10)
- Add to telemetry panel: reliability score, letter grade, glitch count
- Show per-metric breakdown (CC, cognitive, hints)

**T31.5 — Dashboard layout update** (Cx: 10)
- Modify `dashboard.html` to add right panel for code terminal
- Responsive layout that accommodates the new panels
- Wire new JS modules into `main.js`

---

## Dependency Between Sprints

```
Sprint 29 (car project loader) ✅
         ↓
Sprint 30 (league system) ← uses _loaded_parts, code_quality
         ↓
Sprint 31 (viewer) ← uses call_logs, league info in replay
```

Sprint 30 and 31 are sequential — the league system needs to be tested before building the viewer around it. But Sprint 31's call log export (T31.1) is independent of the league system and could be started early.

---

## What This Achieves

After both sprints:
- A new player forks `cars/default_project/`, writes 3 functions, submits to F3
- They see their code executing live in the viewer, with glitches highlighted
- Their quality report shows "CC 8 in gearbox.py — at F1 level this would cost 0.5s/lap"
- They improve code quality, add 3 more parts, qualify for F2
- Eventually implement all 10 parts with A-grade reliability for Championship

This is the full progression path from "I just started" to "I'm competing at the highest level." The physics determines who wins. The code quality determines reliability. The league system structures the journey.
