# NPC Race Roadmap: Sprints 9-16

> From "optimization puzzle" to "racing game." Each sprint adds a layer that makes the next one matter more.

## The Sequence

| Sprint | Name | What It Adds | Why It Matters |
|--------|------|-------------|----------------|
| **9** | **Collision + Safety Car** | Contact detection, damage model, spin risk, safety car | Makes races unpredictable. Perfect strategy wins 60%, adaptation wins 40%. |
| **10** | **Weather System** | Dry→damp→wet→drying transitions, intermediates, full wets | Transforms strategy. Wrong tire = 30s lost. Right call = 5 positions gained. |
| **11** | **ERS + Brake Temp** | Battery deploy/harvest, brake heat/fade, engine wear | More decisions per lap. Attack vs defend vs conserve on three axes. |
| **12** | **Information Asymmetry** | Hidden opponent data, inference from lap times | Strategy under uncertainty. You guess; you can be wrong. |
| **13** | **Narrative Engine** | Battle detection, auto-commentary, race reports | The race tells a story. Moments get names. |
| **14** | **Sound Overhaul** | Spatial audio, per-car engine, crowd, pit sounds | Close your eyes and know it's a race. |
| **15** | **Viewer Polish** | TV Director camera, 3-letter labels, broadcast feel | Looks like a real broadcast. |
| **16** | **Championship Mode** | Multi-race season, points, car development between races | The metagame. Win the season, not just the race. |

## Sprint 9: Collision + Safety Car (Detail Plan)

### New Modules

```
engine/collision.py     (~100 LOC)  Contact detection + outcome
engine/damage.py        (~80 LOC)   Damage model + performance effects
engine/safety_car.py    (~100 LOC)  SC state machine + field compression
engine/incident.py      (~60 LOC)   Spin/lockup probability + resolution
```

### The Physics

**Contact detection:** Two cars collide when:
- Distance gap < 3.0 sim units (roughly 1 car length)
- Lateral difference < 0.25 (same part of track)
- Neither car is in pit lane

**Contact outcome** (probabilistic):
- 50%: both cars lose 5-15 km/h speed (minor contact)
- 30%: one car spins (3-5 second time loss)
- 15%: front wing damage (aero penalty for rest of race)
- 5%: retirement (DNF)

**Spin probability:** Each tick, compute spin risk:
- Base: 0.0001 per tick (very low)
- × grip_deficit_factor (if demanding more than available: risk rises fast)
- × dirty_air_factor (dirty air amplifies)
- × tire_wear_factor (worn tires = higher risk)
- × cold_tire_factor (first 2 laps after pit = risky)
- If random() < spin_risk: spin event → lose 3-5 seconds, position drop

**Damage model:**
- `damage` float 0.0-1.0 (0=perfect, 1=destroyed)
- Front wing damage: aero effectiveness × (1 - damage)
- Accumulates from contacts
- Can be partially repaired in pit stop (adds time)

**Safety car:**
- Triggered by: DNF (100%), spin in high-curvature zone (20%), multi-car contact (40%)
- Duration: 3-5 laps
- Effect: all cars slow to SC pace (~120 km/h), gaps close to 1.0s
- Pit window opens (reduced time loss under SC)
- Restart: 1-lap warning, then green flag

### Strategy State Additions

```python
state["damage"]              # 0.0-1.0 accumulated damage
state["spin_risk"]           # 0.0-1.0 current spin probability
state["safety_car"]          # bool — SC currently active
state["safety_car_laps"]     # int — laps remaining under SC (0 if not active)
state["contact_last_lap"]    # bool — had contact this lap
```

### Strategy Return Additions

```python
"aggression": float  # 0.0-1.0 — how aggressively to defend/attack laterally
                     # Higher = more overtake attempts but higher spin/contact risk
```

## Sprint 10: Weather System

### Core Mechanic

Track wetness: 0.0 (bone dry) → 1.0 (standing water)
- Grip multiplied by: `1.0 - wetness * 0.6` on dry tires
- Intermediates: optimal at wetness 0.3-0.6
- Full wets: optimal at wetness 0.6-1.0
- Wrong compound: catastrophic grip loss

### Weather Model

```
sunshine → clouds → drizzle → rain → heavy rain → drying
```

Each transition is probabilistic. Weather forecast available to strategies but can be wrong.

### Strategy Impact

The strategy function gets:
```python
state["track_wetness"]       # 0.0-1.0
state["weather_forecast"]    # list of (lap, predicted_wetness) — can be inaccurate
state["tire_compound"]       # now includes "intermediate", "wet"
```

## Sprint 11: ERS + Brake Temp

### ERS (Energy Recovery System)

Battery: 0-4 MJ capacity
- Deploy: 120kW boost for up to 33s/lap
- Harvest: braking regenerates energy (MGU-K)
- Turbo harvest: unlimited (MGU-H)

Strategy gets:
```python
state["ers_energy"]          # 0.0-4.0 MJ remaining
state["ers_deploy_mode"]     # "attack" / "balanced" / "harvest"
```

### Brake Temperature

Like tire temp but for brakes:
- Heavy braking → heats
- Airflow → cools
- Hot brakes → fade → longer braking distances
- Affects corner entry speed

## Sprint 12: Information Asymmetry

### What You See vs Reality

During race (strategy function):
- YOUR car: full data (tire_wear, fuel, damage, everything)
- Opponents: position, speed, gap, compound, tire_age_laps ONLY
- No opponent tire_wear, fuel_pct, damage, tire_temp, engine_mode

Post-race (dashboard diagnostic):
- Full data for YOUR car
- Full data for ALL cars (the "download" you can't get during race)

### Inference System

Smart agents can infer opponent state:
- "Their lap times are dropping 0.15s/lap → tires degrading"
- "They pitted for softs 8 laps ago → wear ~0.4 estimated"
- "They're slow in sector 2 → possible damage or fuel saving"

## Sprint 13: Narrative Engine

### Auto-Commentary

Text overlays during race:
- "BATTLE: GooseLoose vs Silky — 3 laps, gap 0.8s"
- "OVERTAKE: GooseLoose passes Silky at Turn 4!"
- "PIT STOP: BrickHouse → Medium tires, 22.3s"
- "RAIN INCOMING: Forecast shows wet in 5 laps"
- "SAFETY CAR: Collision at Turn 7, GooseLoose and GlassCanon"

### Race Report

Auto-generated at race end:
```
MONZA GP — RACE REPORT
Winner: GooseLoose (medium-soft strategy, 1 stop)
Decisive moment: Lap 23, sector 2 — GlassCanon's soft tires
hit the cliff, dropping 1.2s. GooseLoose's mediums held firm.
Safety car on lap 35 bunched the field. SlipStream gambled on
fresh softs and charged from P5 to P3 in the final 10 laps.
Driver of the day: SlipStream (+2 positions in final stint)
```

## Sprint 14: Sound Overhaul

### Spatial Audio Model

- Camera distance to each car → volume per car
- Onboard cam: engine dominant, wind noise, tire squeal
- Follow cam: engine + ambient, crowd at corners
- Full track: ambient wash, crowd swells at overtakes
- Pit row: louder when camera near pit wall

### Engine Synthesis

- Per-car pitch based on speed/RPM (sawtooth + harmonics)
- Turbo whistle on deceleration
- Downshift pops on braking
- Crowd roar proportional to "drama score" (close battles, overtakes)

## Sprint 15: Viewer Polish

### TV Director Camera

Auto-camera that follows the action:
- Default: leader
- Switch to battle when two cars within 1.0s for 3+ laps
- Snap to overtake moment (2s before, 3s after)
- Show pit stop (cut to pit cam for 5s)
- Cut to wide view on safety car restart

### Visual Polish

- 3-letter car abbreviations (not full names)
- Car color-matched labels
- Sector markers on track
- DRS zones visible as blue tint
- Tire marks on racing line (already exists but may need refinement)

## Sprint 16: Championship Mode

### Season Structure

- 10-20 race calendar (subset of our 20 tracks)
- Points per race: 25/18/15/12/10/8/6/4/2/1 (F1 system)
- Championship standings tracked across races
- Car development: earn "development points" from finishing positions
  - Spend points to improve POWER/GRIP/WEIGHT/AERO/BRAKES between races
  - Budget cap: can't max everything

### Cross-Race Learning

Already have the foundation (Sprint 4 learning system):
- Cars learn per-track optimal strategies
- Tournament mode runs multi-race championships
- Data persists between races in cars/data/*.json

### The Metagame

The player writes ONE strategy function that must work across:
- Fast tracks (Monza) — low downforce, long straights
- Technical tracks (Monaco) — high downforce, tight corners
- Wet races — tire compound switching
- After collisions — adapting to damage
- Under safety car — pit timing

The strategy that adapts to ALL conditions wins the championship.
