# Proposal: Digital Training Wheels — Progressive Learning Game Loop

> Status: Draft | Date: 2026-03-26

## Problem

The game is too hard, too slow, and too opaque for new players.

| Issue | Impact | Evidence |
|-------|--------|----------|
| 2-3 min per race iteration | Experimentation is painful | 20 cars × 10 parts × 1ms timeout × 30Hz = 6x realtime |
| Player always finishes P17-P20 | No sense of progress | 20/20/20/20/20 stats vs Berserker 30/22/16/15/17 |
| Gearbox "improvement" made it slower | Trust destroyed | 11000 RPM should be faster but random seed/sim variance masks it |
| No feedback on WHY you're slow | Can't learn | Just a position number, no "you lost 0.5s in sector 2" |
| No solo practice mode | Can't isolate variables | Always racing 19 rivals with traffic/drafting noise |

## Design Philosophy: Adversarial Agents as Teachers

Instead of tutorials or docs, the game teaches through **adversarial
agents** — AI opponents that are calibrated to lose to you at the
right moment, then get harder as you improve.

### The Coaching Ghost

Every player gets a **Ghost** — a virtual opponent that:
1. Starts slightly SLOWER than your current car
2. Uses the SAME part functions as you, but with one deliberate flaw
3. Shows you what it's doing wrong (visible telemetry)
4. Gets faster after you beat it

The Ghost is your teacher. Beat the Ghost → learn the lesson →
Ghost gets harder → new lesson.

### Progressive Adversary Ladder

```
Level 1: Ghost shifts at 14000 RPM (over-revving)
         You: shift at 12800 (default) → you win
         Lesson: "Lower shift points are better"

Level 2: Ghost shifts at 12800 (your old setting)
         You: must shift at ~11000 to beat it
         Lesson: "Torque plateau is 10800-12500 RPM"

Level 3: Ghost has optimal gearbox but bad cooling (effort=1.0)
         You: must tune cooling to beat it
         Lesson: "Less cooling = less drag = faster"

Level 4: Ghost has optimal gearbox + cooling but no pit strategy
         You: must add pit timing to beat it (3-lap race)
         Lesson: "Pit stops matter on longer races"

Level 5: Ghost is a real rival (Tortoise — backmarker)
         You: must beat the weakest real car
         Lesson: "You're ready for the grid"
```

## Solution: Three-Mode Progressive Loop

### Mode 1: Time Trial (5-10 seconds)

**Just your car. One lap. Instant feedback.**

```
npcrace trial --track monza
```

- Runs PartsRaceSim with 1 car, 1 lap
- No rivals, no drafting, no O(n²) — pure physics
- Skip safe_call threading overhead (trusted local code)
- Shows: lap time, sector splits, efficiency breakdown

Output:
```
TIME TRIAL — Monza

  Lap time:  1:27.370

  EFFICIENCY BREAKDOWN
  ├── Gearbox:    0.93  ← shifts at 12,800 RPM (past peak torque)
  ├── Cooling:    0.88  ← effort 0.80 is high drag
  └── Strategy:   1.00  (not applicable in time trial)

  Tip: Peak torque is 10,800-12,500 RPM. Try shifting at 11,000.
```

**Target wall time: < 10 seconds for 1 lap.**

How to achieve this:
- Skip safe_call timeout wrapper for local mode (direct function call)
- No replay recording
- No narrative/drama/commentary processing
- No league validation output
- Accumulate only: lap time, sector times, per-part efficiency scores

### Mode 2: Ghost Race (30-60 seconds)

**You vs one AI opponent. Head-to-head.**

```
npcrace ghost --track monza --level 2
```

- Runs PartsRaceSim with 2 cars: you + Ghost
- Ghost's level determines its flaw
- 1-3 laps depending on level
- Shows: side-by-side comparison

Output:
```
GHOST RACE — Monza (3 laps) — Level 2

  Your Car:    4:15.2  (gearbox: 0.99, cooling: 0.88)
  Ghost:       4:18.7  (gearbox: 0.93, cooling: 0.88)

  You won by 3.5 seconds!

  Ghost was shifting at 12,800 RPM. You shifted at 11,000.
  That's worth ~1 second per lap on this track.

  NEXT: Level 3 — Ghost has optimal gearbox but bad cooling.
  Run: npcrace ghost --track monza --level 3
```

### Mode 3: Grid Race (2-3 minutes)

**Full 20-car race. This is the "real" game.**

```
npcrace run --car-dir cars --track monza --laps 3
```

Unchanged from current, but now the player arrives here AFTER
beating Levels 1-5 and actually understanding the mechanics.

## Implementation: The Ghost System

### Ghost Car Generator

```python
# engine/ghost.py

GHOST_LEVELS = {
    1: {
        "name": "Ghost",
        "color": "#666666",
        "flaw": "gearbox",
        "gearbox_shift_rpm": 14000,  # Way too high
        "cooling_effort": 0.8,
        "description": "Over-revving engine",
    },
    2: {
        "name": "Ghost",
        "flaw": "gearbox",
        "gearbox_shift_rpm": 12800,  # Default (suboptimal)
        "cooling_effort": 0.8,
        "description": "Shifting past peak torque",
    },
    3: {
        "name": "Ghost",
        "flaw": "cooling",
        "gearbox_shift_rpm": 11000,  # Optimal
        "cooling_effort": 1.0,       # Max cooling = max drag
        "description": "Overcooling (too much drag)",
    },
    4: {
        "name": "Ghost",
        "flaw": "strategy",
        "gearbox_shift_rpm": 11000,
        "cooling_effort": 0.3,
        "pit_never": True,           # Never pits
        "description": "No pit strategy",
    },
    5: {
        "name": "Tortoise",
        "flaw": None,                # Real rival car
        "use_rival": "tortoise",
        "description": "Weakest rival — beat it to join the grid",
    },
}
```

### Efficiency Breakdown (The "Coaching" Output)

After every time trial/ghost race, show per-part efficiency:

```python
# engine/coaching.py

def generate_coaching(sim, car_name):
    """Generate coaching tips from efficiency data."""
    call_log = sim.call_logs[car_name]
    tips = []

    gb_eff = avg(e["efficiency"] for e in call_log if e["part"] == "gearbox")
    if gb_eff < 0.95:
        peak_rpm = get_torque_peak()  # 10800-12500
        tips.append(f"Gearbox efficiency: {gb_eff:.0%} — "
                    f"peak torque is {peak_rpm[0]:,}-{peak_rpm[1]:,} RPM")

    cool_eff = avg(e["efficiency"] for e in call_log if e["part"] == "cooling")
    if cool_eff < 0.90:
        tips.append(f"Cooling efficiency: {cool_eff:.0%} — "
                    f"try reducing cooling effort (less drag)")

    return tips
```

### Time Trial Fast Path

Skip everything that doesn't affect a solo car:

```python
# engine/time_trial.py

def run_time_trial(car, track_name, laps=1):
    """Ultra-fast single-car lap. No rivals, no drama, no replay."""
    # Direct function calls (no safe_call threading)
    # No replay recording
    # No narrative processing
    # Return: lap_time, sector_times, efficiency_breakdown
```

Estimated performance:
- 30Hz × ~80s lap = 2,400 ticks
- 10 part calls per tick = 24,000 calls
- Direct call (no thread overhead): ~0.01ms each
- Total: ~0.24 seconds for physics
- **Under 1 second for a 1-lap time trial**

## Player Journey Map

```
MINUTE 0-2:
  npcrace init my_car
  npcrace trial --track monza
  → See lap time + efficiency breakdown
  → "Your gearbox shifts at 12,800 RPM (past peak torque)"

MINUTE 2-5:
  Edit gearbox.py (shift at 11,000)
  npcrace trial --track monza
  → Lap time drops 1 second
  → "Gearbox efficiency: 93% → 99%"
  → AHA MOMENT

MINUTE 5-10:
  npcrace ghost --track monza --level 1
  → Beat the Ghost easily (it shifts at 14,000)
  → "Next: Level 2"
  npcrace ghost --track monza --level 2
  → Close race — Ghost shifts at 12,800 (your old setting)
  → Must have good gearbox to win

MINUTE 10-15:
  npcrace ghost --track monza --level 3
  → Ghost has perfect gearbox but bad cooling
  → Must tune cooling to win
  → Learn cooling tradeoff

MINUTE 15-20:
  npcrace ghost --track monza --level 4
  → 3-lap race, Ghost never pits
  → Must add pit strategy to win

MINUTE 20-25:
  npcrace ghost --track monza --level 5
  → Racing Tortoise (real rival)
  → Beat it = "You're ready for the grid!"

MINUTE 25+:
  npcrace run --car-dir cars --track monza --laps 3
  → Full 20-car race
  → Player finishes mid-pack (not P20) because they've learned
  → Leaderboard, qualifying, multi-track campaigns
```

## Stat Rebalancing

The default car (20/20/20/20/20) is too weak. Options:

### Option A: Boost default stats
Change to 25/20/15/25/15 (100 budget, but optimized for speed).
Player starts mid-pack instead of last.

### Option B: Handicap system
Apply a "rookie bonus" multiplier (1.05x speed) that fades as
the player improves. Creates artificial competitiveness early.

### Option C: Tiered rivals (recommended)
Instead of racing all 19 rivals immediately, race only your tier:
- F3 Rookies (4 cars): Tortoise, RustBucket, PaperWeight, SteamRoller
- F3 Midfield (5 cars): IronSide, CrossWind, FoxFire, DriftKing + you
- Full grid only after beating all F3 Rookies

**Recommendation: Option C.** It uses existing cars, no physics changes,
and naturally creates a progression ladder.

## Execution Plan

### Sprint 45: Time Trial + Coaching (12 Cx)

1. `engine/time_trial.py` — fast single-car sim, direct function calls (< 1s)
2. `engine/coaching.py` — efficiency breakdown + actionable tips
3. `npcrace trial` CLI command with formatted output
4. Efficiency data added to PartsRaceSim frame export (for live HUD)
5. Integration gate: trial → edit → trial → see improvement

### Sprint 46: Ghost System + Viewer Integration (15 Cx)

1. `engine/ghost.py` — ghost level definitions (5 levels)
2. `engine/ghost_race.py` — 2-car race with comparison output
3. `npcrace ghost` CLI command
4. Ghost car in viewer: translucent rendering + split telemetry
5. Live efficiency HUD in viewer dashboard (WebSocket frame extension)
6. Ghost vs player comparison view (efficiency side-by-side)

### Sprint 47: Tiered Grid + Progression (10 Cx)

1. Tier system in car_loader (rookies, midfield, full grid)
2. `npcrace run` defaults to your tier
3. `--full-grid` flag for full 20-car race
4. Progression tracking (beat Ghost Level 5 → unlock full grid)
5. Ghost optional on any track after first completion

## Decisions (Approved)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Safe call modes | **Two modes.** Local: skip safe_call (direct calls, < 1s). Server: use safe_call (sandboxed, slower). | Local code is trusted. Server code is not. Performance ceiling for local play is non-negotiable. |
| Ghost per-track | **Ghost is optional after track one.** Beat Ghost Level 5 on any track → unlocked globally. Ghost available on any track after that but not required. | First track teaches mechanics. After that, player chooses their own path — ghost for practice, grid for competition. |
| Ghost in viewer | **Both viewable.** Ghost appears in the dashboard viewer alongside your car. Split telemetry shows your efficiency vs Ghost's efficiency side-by-side. | Visual racing is the game's strongest asset. Text comparison alone wastes it. Seeing the Ghost pull away in turns because of bad cooling is 10x more educational than a number. |
| Efficiency HUD | **During the race.** Live efficiency overlay in the dashboard shows per-part scores updating in real-time as you race. Post-race summary also shown. | Live feedback creates the "I see what's happening" moment. Watching gearbox efficiency drop from 0.99 to 0.85 as RPM climbs past the torque peak teaches the concept viscerally. |

## Live Efficiency HUD Design

The viewer dashboard already has telemetry panels. Add an efficiency
overlay that streams alongside the race:

```
┌─ EFFICIENCY (live) ──────────────────┐
│  Gearbox:  ████████░░  0.93  ← RPM  │
│  Cooling:  ██████████  0.99         │
│  Strategy: ████████░░  0.92         │
│  ─────────────────────────────────── │
│  Product:  ████████░░  0.85         │
└──────────────────────────────────────┘
```

### Implementation
- PartsRaceSim already computes per-part efficiency every tick
  (`engine/efficiency_engine.py:354`)
- Stream efficiency data in the WebSocket frame alongside position/speed
- Viewer JS reads `frame.efficiency` dict and renders bars
- Ghost race: show two columns (your car vs Ghost)

### Ghost in Viewer
- Ghost car rendered as translucent/dimmed version on the track canvas
- Ghost telemetry shown in a second column
- When Ghost is ahead: red highlight. When behind: green.
- Split time delta shown: "+0.3s" or "-0.5s" at each sector
