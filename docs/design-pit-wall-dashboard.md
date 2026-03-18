# Pit Wall Dashboard — Design Report

> Sprint 8 Planning Document. Research-backed design for an F1-style pit wall viewer.

## Vision

The viewer transforms from "watch a race" to **"run a pit wall"**. The track animation shrinks to one panel. The rest of the screen is dense, scientific telemetry — monospaced numbers, time-series sparklines, sector deltas in purple/green/yellow. It should feel like you're the race engineer, not a TV viewer.

The feedback loop: **I see my car lost 0.3s in sector 2 because dirty air killed grip → I go change my strategy code → I run again → sector 2 is green.**

## Layout: 4-Zone Grid

```
┌──────────────────────────────────────────────────────────────────────────┐
│ STATUS BAR (full width, 32px)                                           │
│ Lap 12/53  │  Race Time 0:42:17  │  Flag: GREEN  │  Track: Monza 28°C  │
├─────────────┬────────────────────────────┬───────────────────────────────┤
│ TIMING      │ TRACK VIEW                 │ CAR TELEMETRY                 │
│ TOWER       │ (compact, ~40% width)      │ (selected car, ~30% width)    │
│ (~15%)      │                            │                               │
│             │  ┌──────────────────┐      │  ▶ GooseLoose                 │
│ P1 GOO +0.0│  │                  │      │  ────────────────────────────  │
│   M 12 laps│  │   [track map     │      │  Speed    287 km/h            │
│ P2 ▶SLK+1.2│  │    with cars]    │      │  Tire     ██████░░ 62% MED    │
│   M 12 laps│  │                  │      │  Temp     94°C  [optimal]     │
│ P3 GLC +2.1│  │                  │      │  Fuel     ███████░ 71%        │
│   S  8 laps│  │                  │      │  Wear/lap 0.031               │
│ P4 SLP +3.4│  │                  │      │  DRS      READY               │
│   M 12 laps│  │                  │      │  Mode     PUSH                │
│ P5 BRK +8.1│  │                  │      │  Dirty    ▓▓░ 0.94           │
│   H 12 laps│  └──────────────────┘      │  Pit #    1 (lap 18)         │
│             │                            │  Gap ▲    +1.203s            │
│ Best Lap:   │                            │  Gap ▼    -0.892s            │
│ 1:02.334    │                            │                               │
│ GOO (lap 8) │                            │  SECTORS (vs best)            │
│             │                            │  S1  32.1  🟢 -0.2           │
│             │                            │  S2  31.8  🟣 -0.4  BEST     │
│             │                            │  S3  ...running...            │
├─────────────┴────────────────────────────┴───────────────────────────────┤
│ TELEMETRY STRIP (full width, ~200px height, time-series)                │
│                                                                          │
│ Speed ─────╱╲────╱╲────╱╲────╱╲────╱╲────╱╲────╱╲────╱╲─────           │
│ 350 ┤                                                                    │
│ 200 ┤     ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲                         │
│  50 ┤────╱    ╲╱    ╲╱    ╲╱    ╲╱    ╲╱    ╲╱                         │
│     └─────────────────────────────────────────────── lap 11  12  13     │
│                                                                          │
│ Tire ──────────────────────────╱                    Wear (green=ok)      │
│ Temp ─────────────────────────╱                     Temp (blue→red)      │
│ Gap  ──────╲__________╱─────────╲_____              To leader (white)    │
│                                                                          │
│ ● = pit stop    ▲ = overtake    ▼ = lost position    ◆ = dirty air zone │
└──────────────────────────────────────────────────────────────────────────┘
```

## Zone Details

### Zone 1: Status Bar (top, full width, 32px)

Fixed header. Always visible.

| Element | Format | Source |
|---------|--------|--------|
| Lap counter | `Lap 12/53` | `frame.lap` / `replay.laps` |
| Race clock | `0:42:17` | `frame.elapsed_s` |
| Flag status | `GREEN` / `SAFETY CAR` / `FINAL LAP` | derived from lap |
| Track name | `Monza` | `replay.track_name` |
| Track temp | `28°C` | future (static for now) |

### Zone 2: Timing Tower (left column, ~15% width)

Vertical leaderboard. Updates every frame.

Per car row (50px height):
```
P1  GOO  +0.000s   M  12 laps  ██ 62%
    ^^^  ^^^^^^^^   ^  ^^^^^^^  ^^^^^^
    abbr gap-to-    tire  tire   wear
         leader     comp  age    bar
```

**Color coding:**
- Position number: white
- Gap: white (gaining = bright), yellow (losing)
- Selected car row: highlighted background
- Car color stripe: left edge, 4px wide
- Tire compound: red dot (S), yellow dot (M), white dot (H)

**Fastest lap indicator:** Purple dot next to car that holds fastest lap.

Click any car row → right panel switches to that car's telemetry.

### Zone 3: Track View (center, ~40% width)

Compact top-down track map. Same rendering as current viewer but smaller. Shows:
- All car positions as colored dots
- Selected car highlighted (larger, pulsing border)
- Sector boundaries as dashed lines (S1/S2/S3)
- DRS zones as blue-tinted track sections
- Dirty air zones: orange haze behind leading cars

**NOT the main focus.** Peripheral awareness only.

### Zone 4: Car Telemetry Panel (right column, ~30% width)

Deep dive on the selected car. This is where the feedback loop lives.

**Header:** Car name + color + team identity
```
▶ GooseLoose
──────────────────────────
```

**Live Readouts** (monospaced, tabular):
```
Speed     287 km/h        ← large font
Tire      ██████░░ 62%    ← bar + percentage
  Compound  MEDIUM (12 laps old)
  Temp      94°C [OPTIMAL] ← green/yellow/red
  Wear/lap  0.031         ← computed client-side
Fuel      ███████░ 71%    ← bar + percentage
  Burn rate 2.1 kg/lap
DRS       READY           ← or ACTIVE (green) or UNAVAIL (gray)
Engine    PUSH            ← red for push, white for std, blue for conserve
Dirty Air ▓▓░ 0.94       ← bar showing grip factor, orange when active
Pit Stops 1 (last: lap 18, soft→medium)
Gap ▲     +1.203s (to P1) ← gap to car ahead
Gap ▼     -0.892s (to P3) ← gap to car behind
```

**Sector Comparison Table:**
```
        Current    Best     Delta
S1      32.112    31.890    +0.222  ← YELLOW (slower)
S2      31.456    31.890    -0.434  ← PURPLE (session best!)
S3      ...running...
Lap     ...
```

Colors: 🟣 purple = overall best, 🟢 green = personal best, 🟡 yellow = slower

**"Aha Moment" Alerts** (flash + fade, bottom of panel):
```
⚠ DIRTY AIR: Lost 0.08 grip in Turn 4 (sector 2)
⚠ TIRE CLIFF: Wear at 0.78, cliff at 0.80!
✓ UNDERCUT: Pit stop gained P2 → P1 (+1 position)
⚠ FUEL CRITICAL: 3 laps of fuel remaining at current rate
```

### Zone 5: Telemetry Strip (bottom, full width, ~200px)

Time-series graphs showing the last 3 laps (rolling window). X-axis = distance around track (or time). Multiple traces stacked:

**Row 1: Speed trace** (primary, tallest ~80px)
- White line = current car
- Gray line = previous lap overlay (ghosted)
- Curvature shading underneath (light gray = straight, dark = corner)
- Vertical markers at sector boundaries

**Row 2: Tire wear + temp** (~40px)
- Green line = tire wear (0→1 scale)
- Orange line = tire temp
- Red dashed line = cliff threshold
- Pit stop markers (vertical line with compound label)

**Row 3: Gap to leader** (~40px)
- White line trending
- Green fill when gap shrinking, red fill when growing
- Pit stop markers show gap jumps

**Event markers on all rows:**
- ● = pit stop
- ▲ = overtake gained
- ▼ = position lost
- ◆ = dirty air zone entered

### Post-Race: Full Diagnostic Mode

When race ends, a toggle appears: **"VIEW FULL DIAGNOSTIC"**

This switches the bottom strip to a full-race timeline:
- All laps, not rolling window
- Lap time bar chart (colored by compound, highlighted with best lap)
- Tire strategy timeline (horizontal bars per stint)
- Cumulative gap chart
- Sector-by-sector breakdown table

**Only available for the player's car.** Clicking other cars in the tower shows their live data during replay but the diagnostic is locked to your car.

## Color Language

| Color | Meaning | Hex |
|-------|---------|-----|
| Purple | Session best (any car) | `#a855f7` |
| Green | Personal best (selected car) | `#22c55e` |
| Yellow | Slower than personal best | `#eab308` |
| Red | Danger / alert / push mode | `#ef4444` |
| Blue | Conserve mode / DRS zone | `#3b82f6` |
| Orange | Dirty air / warning | `#f97316` |
| White | Neutral / gaining / standard | `#e0e0e0` |
| Gray | Inactive / historical / unavailable | `#6b7280` |

## Typography

- **Readouts:** `JetBrains Mono` (monospaced, tabular figures)
- **Headers:** `Outfit` or similar sans-serif (already loaded)
- **Numbers:** Always right-aligned, 3 decimal places for times
- **Sector deltas:** Signed (`+0.222` / `-0.434`), colored

## Data Requirements

### Already in replay frames:
speed, tire_wear, tire_temp, tire_compound, fuel_pct, engine_mode, drs_active, pit_status, lateral, in_dirty_air, elapsed_s, gap_ahead_s, current_sector, position, lap

### Needs to be added to replay frames:
| Field | Purpose | Source |
|-------|---------|--------|
| `gap_behind_s` | Defensive gap readout | Compute from positions |
| `last_lap_time` | Lap time display + deltas | From timing module |
| `best_lap_s` | Personal best reference | From timing module |
| `sector_time` | Sector comparison table | From timing module (on sector completion) |
| `tire_age_laps` | Tire age display | Already in state, not exported |
| `pit_stops` | Pit count display | From pit_state |
| `dirty_air_factor` | Numerical grip loss readout | Already computed, need to export |

### Needs to be added to results:
Already have: total_time_s, best_lap_s, lap_times, pit_stops ✓

### Computed client-side (no engine changes):
- Wear rate per lap (delta tire_wear across laps)
- Fuel burn rate (delta fuel_pct across laps)
- Gap trend (is gap growing or shrinking?)
- Sector deltas (current vs best)
- Overtake events (position changes frame-to-frame)
- Pit stop duration (pit_entry → racing transition)

## Implementation Approach

### Sprint 8 Task Breakdown (proposed)

**Wave 1 (parallel):**
- T8.1: Replay enrichment — add missing fields (gap_behind_s, last_lap_time, best_lap_s, sector_time, tire_age_laps, pit_stops, dirty_air_factor)
- T8.2: Dashboard HTML/CSS layout — 4-zone grid, status bar, timing tower, telemetry panel, strip area. No JS logic yet, just structure + styling with mock data.

**Wave 2 (parallel):**
- T8.3: Timing tower JS — live position list, gap updates, tire indicators, click-to-select, fastest lap marker
- T8.4: Car telemetry panel JS — live readouts, sector comparison table, aha-moment alerts
- T8.5: Telemetry strip JS — speed trace, tire/gap sparklines, event markers

**Wave 3:**
- T8.6: Post-race diagnostic mode — full-race timeline, lap time chart, strategy breakdown
- T8.7: Integration gate — play.py serves new viewer, all panels work with real race data

## What "Scientific, Not Flashy" Means in Practice

- No gradients, no shadows, no rounded corners on data panels
- No animations on numbers (instant update, not animated counters)
- Monospaced fonts everywhere data appears
- Dense: minimize padding, maximize information per pixel
- Color means something — never decorative
- Dark background, high contrast text (#1a1a2e bg, #e0e0e0 text)
- Grid lines on charts: subtle, 1px, #2a2a3e
- Numbers to 3 decimal places (1:02.334, not "about a minute")
- Right-aligned numbers, tabular figure spacing
- Every element answers a question — no "filler" UI

## Interaction Model

- **Default state:** Race plays, player's car selected, rolling 3-lap window
- **Click timing tower row:** Switch telemetry panel to that car
- **Scrubber:** Drag to any point in race (same as now)
- **Play/Pause:** Same controls
- **Speed:** 0.5x / 1x / 2x / 4x (same as now)
- **End of race:** "FULL DIAGNOSTIC" button appears
- **Skip to end:** Works but feels cheap (scrubber goes to 100%)
- **Keyboard:** `1-5` select car by position, `D` toggle diagnostic, `T` toggle timing tower

## File Size Concern

Current viewer.html + 8 JS files. The dashboard adds significant JS. May need to split into:
- `js/dashboard-layout.js` — grid, panels, resize handling
- `js/timing-tower.js` — leaderboard rendering
- `js/telemetry-panel.js` — car readouts + alerts
- `js/telemetry-strip.js` — time-series charts
- `js/diagnostic.js` — post-race analysis view

Total estimated: ~800-1200 LOC of new JS across 5 files.
