# Sprint 33 — Leaderboard + Onboarding (Final Sprint)

> Closes the local product loop. After this sprint, the game is complete for local play.

## Context

Sprints 23-32 built the engine (physics, code quality, car loader, leagues, viewer, submission). The product loop is:

```
Player writes code → npcrace run → results.json → npcrace submit → "Verified"
```

What's missing: **somewhere for results to go** and **a way for new players to start**.

## Scope

### Part 1: Local Leaderboard

A persistent local leaderboard that accumulates results across races.

**`engine/leaderboard.py`**:
- `load_leaderboard(path)` → dict of standings
- `add_result(leaderboard, results_summary)` → updated standings
- `save_leaderboard(leaderboard, path)` → persist to JSON
- `format_standings(leaderboard)` → printable table

**Standings format:**
```json
{
  "version": "1.0",
  "last_updated": "2026-03-23T12:00:00Z",
  "entries": [
    {
      "name": "MyCarProject",
      "league": "F3",
      "races": 5,
      "wins": 2,
      "podiums": 4,
      "best_lap_s": 80.12,
      "avg_position": 1.8,
      "total_points": 95,
      "reliability_score": 0.94
    }
  ]
}
```

**CLI: `npcrace leaderboard`**
- `npcrace leaderboard` — show current standings
- `npcrace leaderboard --add results.json` — add a race result to standings
- `npcrace leaderboard --reset` — clear standings

Points system: F1 championship points (25, 18, 15, 12, 10, 8, 6, 4, 2, 1) for P1-P10.

### Part 2: Onboarding

**`GETTING_STARTED.md`** in repo root:
- What NPC Race is (one paragraph)
- Prerequisites (Python 3.11+, pip install)
- Quick start: `npcrace init my_car && npcrace run --car-dir my_car`
- What to change first (gearbox shift points)
- How code quality works (complexity → reliability → glitches)
- How leagues work (F3 → Championship)
- How to submit and track standings

**`npcrace init` polish:**
- Currently creates a cars/ directory. Update to copy `cars/default_project/` as a starter.
- `npcrace init my_car` → creates `my_car/` with car.py, gearbox.py, cooling.py, strategy.py, README.md
- Print: "Created my_car/. Run `npcrace run --car-dir my_car` to race."

## Task Breakdown

### T33.1 — Leaderboard module (Cx: 15)
Create `engine/leaderboard.py` with load/add/save/format functions.
Tests: add results, accumulate across races, points calculation, persistence.

### T33.2 — Leaderboard CLI (Cx: 10, depends: T33.1)
Add `npcrace leaderboard` subcommand with --add and --reset flags.
Wire into cli/main.py and cli/commands.py.

### T33.3 — Onboarding materials (Cx: 10)
Create `GETTING_STARTED.md`. Polish `npcrace init` to copy default_project.
Test: `npcrace init my_car` creates a working project that races.

### T33.4 — Integration gate (Cx: 10, depends: T33.2, T33.3)
End-to-end: init → run → submit → leaderboard add → leaderboard show.
Verify the complete player journey works in sequence.

## Dependency Graph

```
T33.1 (leaderboard module) → T33.2 (CLI) ─┐
T33.3 (onboarding) ────────────────────────┼→ T33.4 (GATE)
```

## After Sprint 33

The game is **complete for local play**. The v3.1 proposal is fully delivered (Phases 1-5b). What comes next is growth:

- **Phase 6 (future)**: Hosted infrastructure — server-side execution, web leaderboard, multiplayer seasons, player accounts. This is product work, not engineering. Build it when there are players, not before.
- **Polish (optional)**: TRON car diagnostic viewer, multi-track leaderboard filtering, replay sharing, documentation site.

The engineering is done. The physics is honest. The game loop works. Ship it and find players.
