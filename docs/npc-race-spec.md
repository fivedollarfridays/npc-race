# NPC Race — Development Spec

## Concept

NPC Race is part of the NPC Series — games where you dont play, you upload code. Everyone gets the same driver AI. Players upload a Python file defining their car's stats and strategy function. The engine runs the race, produces a replay JSON, and an HTML viewer animates it.

Same pattern as NPC Wars: `play.py` launcher, car files in `cars/`, canvas replay viewer.

## Architecture

```
npc-race/
├── engine.py          # Core simulation — track gen, physics, race loop
├── tracks.py          # Named track presets (coordinate arrays)
├── play.py            # CLI launcher
├── viewer.html        # HTML canvas replay viewer (single file, no deps)
├── car_template.py    # Starter template for players
├── replay.json        # Output from race (gitignored)
└── cars/              # Player car files
    ├── gooseloose.py  # Seed car — balanced aggro (founder car)
    ├── slipstream.py  # Seed car — aero drafter
    ├── brickhouse.py  # Seed car — brute power
    ├── silky.py       # Seed car — grip corner carver
    └── glasscanon.py  # Seed car — max power glass cannon
```

No external dependencies. Python stdlib only. Viewer is vanilla HTML/CSS/JS.

---

## Car File Format

Each car is a single `.py` file with module-level constants and one function.

```python
CAR_NAME = "MyCar"        # Display name
CAR_COLOR = "#00ff88"     # Hex color

# Budget: 100 points total across all 5 stats
POWER = 20    # Top speed, acceleration
GRIP = 20     # Cornering speed ceiling
WEIGHT = 20   # Heavier = slower accel, better draft resistance
AERO = 20     # Drafting bonus behind other cars, high speed stability
BRAKES = 20   # Braking power into corners

def strategy(state):
    """Called every tick. Returns dict with throttle, boost, tire_mode."""
    return {
        "throttle": 1.0,                    # 0.0 to 1.0
        "boost": False,                     # one-time use, 3 seconds
        "tire_mode": "balanced",            # "conserve" | "balanced" | "push"
    }
```

### Validation Rules

- All 5 stat fields required, must be numeric >= 0
- Sum of stats must be <= 100 (under budget is allowed)
- CAR_NAME must be a non-empty string
- CAR_COLOR must be valid hex
- strategy() is optional — defaults to full throttle, balanced tires, no boost
- strategy() must return a dict. Missing keys use defaults. Bad return types ignored.
- strategy() exceptions are caught silently — car gets default decisions that tick
- Car files starting with `_` are skipped

### Strategy State Object

Passed to `strategy()` every tick:

```python
{
    "speed": 142.5,              # Current speed
    "position": 3,               # Race position (1 = first)
    "total_cars": 8,             # Cars in race
    "lap": 1,                    # Current lap (0-indexed)
    "total_laps": 3,             # Total laps
    "tire_wear": 0.35,           # 0.0 (fresh) to 1.0 (destroyed)
    "boost_available": True,     # Haven't used boost yet
    "boost_active": False,       # Boost currently firing
    "curvature": 0.18,           # Track curvature at position (0 = straight)
    "nearby_cars": [             # Cars within 100 distance units
        {
            "name": "SlipStream",
            "distance_ahead": 22.5,   # Positive = ahead, negative = behind
            "speed": 138.0,
            "lateral": 0.3,
        }
    ],
    "distance": 1250.0,          # Total distance traveled
    "track_length": 2400.0,      # One lap length
    "lateral": 0.0,              # Lane position -1 to 1
}
```

---

## Physics Engine

### Core Loop

- 30 ticks per second
- Each tick: get strategy decisions → apply physics → update positions → record frame
- Race ends when all cars cross finish or max 10000 ticks

### Speed Model

```
base_max_speed = 160 + (power * 100) - (weight * 25)
```

With boost active: `base_max_speed *= 1.25`

### Cornering

Grip creates an absolute corner speed ceiling independent of power:

```
effective_grip = grip * tire_grip_multiplier
grip_corner_ceiling = 100 + (effective_grip * 200)
corner_penalty = curvature * (4.0 - effective_grip * 3.0)
corner_speed_limit = grip_corner_ceiling * max(0.2, 1.0 - corner_penalty)
corner_speed_limit = max(35, corner_speed_limit)
```

This means high-grip cars maintain speed through corners regardless of power stat. High-power low-grip cars must brake hard for corners.

### Acceleration and Braking

```
mass_factor = 1.0 + (weight * 0.5)
accel_rate = (60 + power * 80) / mass_factor * dt
brake_rate = (80 + brakes * 100) * dt
```

Car accelerates toward target_speed or brakes down to it each tick.

### Drafting

When within 5-40 distance units behind another car:

```
draft_bonus = aero * 8 * (1 - distance_ahead / 40)
speed += draft_bonus * dt
```

### Tire Degradation

Wear rate per tick based on tire_mode:
- conserve: 0.00008
- balanced: 0.00018
- push: 0.00035

Tire wear reduces effective grip: `tire_grip_mult = max(0.3, 1.0 - tire_wear * 0.7)`

### Boost

- One-time use per race
- Lasts 3 seconds (90 ticks)
- Multiplies base_max_speed by 1.25
- Cannot be re-used once activated

### Grid Start

Cars are staggered by 15 distance units based on load order. First loaded car starts closest to the line.

---

## Track System

### Track Generation

Tracks are defined as arrays of control points. The engine uses Catmull-Rom spline interpolation to produce smooth curves (default 500 points per track).

### Named Track Presets (tracks.py)

Model real-world circuit layouts by city/region name. No motorsport series branding. Encode as coordinate arrays that approximate the actual track shapes. Scale tracks to fit an 800x700 canvas.

Required presets — organized by character:

**Power tracks (long straights, heavy braking)**
- Monza (Italy) — cathedral of speed, minimal corners, long straights
- Baku (Azerbaijan) — mega straight into tight 90-degree corners
- Jeddah (Saudi Arabia) — fast street circuit, flowing high-speed
- Spa (Belgium) — long circuit, elevation changes, Eau Rouge S-curve

**Technical tracks (tight corners, low speed)**
- Monaco — tight hairpins, elevation, minimal overtaking
- Singapore — slow street circuit, many 90-degree turns
- Zandvoort (Netherlands) — narrow, banked corners

**Balanced tracks (mixed speed)**
- Silverstone (England) — fast flowing corners, Maggots-Becketts complex
- Suzuka (Japan) — figure-8 layout, mix of fast and slow
- Austin (Texas) — elevation change, flowing S-curves section
- Barcelona (Spain) — reference circuit, tests everything
- Bahrain — heavy braking zones, traction out of slow corners

**Character tracks**
- Interlagos (Brazil) — short, counterclockwise, elevation
- Imola (Italy) — old school narrow, limited runoff feel
- Melbourne (Australia) — street circuit, fast park section
- Montreal (Canada) — stop-start, wall of champions
- Mugello (Italy) — flowing high-speed, elevation
- Lusail (Qatar) — flowing fast, few heavy braking zones
- Hungaroring (Hungary) — tight and twisty, like Monaco without walls
- Shanghai (China) — long back straight, technical middle sector

### Track Data Structure

```python
# tracks.py

TRACKS = {
    "monza": {
        "name": "Monza",
        "country": "Italy",
        "character": "power",
        "laps_default": 5,
        "control_points": [
            (x, y), (x, y), ...  # 10-20 control points defining shape
        ],
    },
    "monaco": {
        "name": "Monaco",
        "country": "Monaco",
        "character": "technical",
        "laps_default": 3,
        "control_points": [ ... ],
    },
}
```

### Track Selection in play.py

```bash
python play.py --track monza
python play.py --track monaco --laps 5
python play.py --track random         # random preset
python play.py --seed 42              # procedural track (current behavior)
python play.py --list-tracks          # print available tracks
```

When using a named track, ignore --seed. When no --track specified, use procedural generation with --seed.

---

## Replay Format (replay.json)

```json
{
    "track": [{"x": 100.0, "y": 200.0}, ...],
    "track_name": "Monza",
    "track_width": 50,
    "laps": 3,
    "ticks_per_sec": 30,
    "car_count": 5,
    "frames": [
        [
            {
                "x": 150.2,
                "y": 210.5,
                "name": "GooseLoose",
                "color": "#ff6600",
                "speed": 142.5,
                "lap": 1,
                "position": 2,
                "tire_wear": 0.35,
                "boost": false,
                "finished": false
            }
        ]
    ],
    "results": [
        {
            "name": "GooseLoose",
            "color": "#ff6600",
            "position": 1,
            "finish_tick": 850,
            "finished": true
        }
    ]
}
```

---

## Viewer (viewer.html)

Single-file HTML/CSS/JS. No build step. No external dependencies except Google Fonts.

### Features

- Canvas rendering of track and car positions
- Drag-and-drop replay.json loading
- Auto-loads replay.json from same directory via fetch
- Playback controls: play/pause, speed (0.5x, 1x, 2x, 4x), scrubber
- Live leaderboard sidebar showing position, speed, tire wear, boost status
- Lap counter
- Start/finish line marker
- Boost glow effect on cars
- Results overlay on race completion
- Track name display in header when available

### Visual Style

- Dark theme (#0a0a0f background)
- JetBrains Mono for data, Outfit for UI text
- Orange (#ff6600) accent color — matches NPC series branding
- Track rendered as thick rounded stroke with dashed center line
- Cars are colored circles with position number inside
- Minimal, functional, not flashy

---

## CLI (play.py)

```
usage: play.py [-h] [--car-dir DIR] [--laps N] [--seed N] [--track NAME]
               [--list-tracks] [--output FILE] [--no-browser]

NPC Race — you build the car, we run the race

options:
  --car-dir DIR     Directory containing car .py files (default: cars)
  --laps N          Number of laps (default: track default or 3)
  --seed N          Track generation seed for procedural tracks (default: 42)
  --track NAME      Named track preset (e.g. monza, monaco, silverstone)
  --list-tracks     Print available tracks and exit
  --output FILE     Replay output file (default: replay.json)
  --no-browser      Don't auto-open viewer
```

---

## Seed Cars

Five cars ship with the game to demonstrate different build philosophies:

| Car | Philosophy | POWER | GRIP | WEIGHT | AERO | BRAKES | Strategy |
|-----|-----------|-------|------|--------|------|--------|----------|
| GooseLoose | Balanced aggro | 25 | 25 | 15 | 20 | 15 | Push tires early, conserve late. Boost on last lap if not P1. |
| SlipStream | Drafter | 20 | 15 | 15 | 35 | 15 | Sits in draft, conserves tires, slingshots with boost when close behind on last lap. |
| BrickHouse | Brute force | 35 | 10 | 25 | 15 | 15 | Full throttle on straights, heavy braking for corners. Boost on straight when behind. |
| Silky | Corner carver | 15 | 35 | 15 | 15 | 20 | Conserves tires early, pushes when others are worn. Boosts in corners on last lap. |
| GlassCanon | Yolo speed | 40 | 15 | 10 | 20 | 15 | Max throttle always, minimal corner management. Pushes tires permanently. Boosts first straight of last lap. |

Different tracks should produce different winners. Power tracks favor GlassCanon/BrickHouse. Technical tracks favor Silky/GooseLoose. This validates the physics balance.

---

## Balance Validation

Run each seed car on 5+ tracks. No single car should win every track. Expected pattern:
- Power tracks: GlassCanon or BrickHouse wins
- Technical tracks: Silky or GooseLoose wins
- Balanced tracks: GooseLoose or SlipStream competitive
- Tire-heavy races (5+ laps): Silky or SlipStream should gain late

If one car dominates all track types, adjust physics constants (corner ceiling formula, draft multiplier, tire wear rates).

---

## What NOT to Build

- No multiplayer/networking — this is local-first, replay-based
- No car file editor or GUI — players write Python
- No leaderboard server — that comes later as a separate service
- No sound — viewer is silent
- No 3D — top-down 2D canvas only
- No car-to-car collision physics — cars pass through each other (drafting only interaction)
- No pit stops — tire strategy is managed via tire_mode only
- No weather — track conditions are static
- No qualifying — grid order is load order

---

## Build Order

1. `tracks.py` — encode all 20 track presets as control point arrays
2. Update `engine.py` — integrate tracks.py, add track selection logic
3. Update `play.py` — add --track and --list-tracks flags
4. Update `viewer.html` — show track name in header
5. Balance test — run all seed cars on all tracks, tune physics if needed
6. `car_template.py` — update with final strategy state docs
7. README.md — player-facing docs: how to make a car, how to race
