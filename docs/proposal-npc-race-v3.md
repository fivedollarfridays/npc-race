# NPC Race v3 — Technical Proposal

> Build a car out of code.

---

## 1. What NPC Race Is

A competitive coding game where players write Python functions that control the mechanical systems of an F1 race car. Every function is a real car part. The physics simulation calls each function every tick. Better engineering decisions — expressed as better code — produce a faster, more reliable car.

The player is the engineering team. The driver is the same world-class AI in every car. The difference between winning and losing is the quality of the code running inside the machine.

---

## 2. The Problem With v2

NPC Race v1-v2 used five abstract stats (`POWER=25, GRIP=25`) and a `strategy()` function. This was a configuration game, not a coding game. The sensitivity test proved it: changing player code by meaningful amounts produced 0.0-0.3 second differences in lap time. The physics didn't care what the code did.

**Root causes:**
- Pre-computed speed profile determined 99% of lap time
- Part function outputs weren't fed back into the speed computation
- No penalty for bad decisions, no reward for good ones
- Additive model: small changes produced small effects that didn't compound

---

## 3. The v3 Architecture

### 3.1 Three Layers

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: PLAYER CODE                               │
│  10 car part functions written in Python             │
│  Each function IS a real F1 car part                 │
│  Runs in a sandboxed environment                     │
├─────────────────────────────────────────────────────┤
│  LAYER 2: PHYSICS ENGINE                             │
│  Real mechanical simulation (simplified Pacejka,     │
│  power model, thermodynamics, energy conservation)   │
│  Calls player code every tick, applies consequences  │
├─────────────────────────────────────────────────────┤
│  LAYER 3: CODE QUALITY → CAR RELIABILITY             │
│  AST-based quality analysis of player's codebase     │
│  Complexity, lint, structure → reliability score      │
│  More complex code = more frequent part glitches     │
└─────────────────────────────────────────────────────┘
```

### 3.2 The 10 Car Parts

Each is a Python function the player writes. The physics engine calls it every simulation tick (30 Hz) with real physical conditions. The function returns a decision. The physics applies consequences.

| # | Part | Inputs | Output | What Bad Code Does |
|---|------|--------|--------|-------------------|
| 1 | `engine_map` | rpm, throttle_demand, engine_temp | (torque_pct, fuel_flow_pct) | Over-fuels: engine overheats. Under-fuels: loses power. Excess torque above traction: wheelspin, tire wear, no extra speed. |
| 2 | `gearbox` | rpm, speed, current_gear, throttle | target_gear (1-8) | Wrong gear: RPM outside torque band, less power. Missed downshift: no engine braking. Late upshift: over-rev wear. |
| 3 | `ers_deploy` | battery_pct, speed, lap, gap_ahead, braking | deploy_kw (0-120) | Depletes battery before overtake zone. Deploys in corner where traction-limited (wasted energy). |
| 4 | `ers_harvest` | braking_force, battery_pct, battery_temp | harvest_kw (0-120) | Overcharges: battery thermal shutdown. Under-harvests: no energy for deployment later. |
| 5 | `brake_bias` | speed, decel_g, grip_front, grip_rear | front_pct (50-65) | Too much front: front lockup, flat spot, can't steer. Too much rear: spin. |
| 6 | `suspension` | speed, lateral_g, bump_severity, ride_height | ride_height_target (-1 to 1) | Too low: bottoms out (20% downforce loss, 10% extra drag). Too high: loses ground effect. |
| 7 | `cooling` | engine_temp, brake_temp, battery_temp, speed | cooling_effort (0-1) | Too little: engine overheats (-2% power per degree above 120°C). Too much: drag penalty slows car. |
| 8 | `fuel_mix` | fuel_remaining_kg, laps_left, position, gap | lambda (0.85-1.15) | Too rich: runs out of fuel. Too lean: loses power when it matters. |
| 9 | `differential` | corner_phase, speed, lateral_g | lock_pct (0-100) | Over-locked in corners: understeer. Under-locked on exit: inside wheelspin. |
| 10 | `strategy` | full telemetry state | {pit, compound, mode} | Wrong pit window. Wrong compound for conditions. Missed safety car opportunity. |

### 3.3 The Multiplicative Model

Each part's decision is evaluated against the theoretical optimum for the current conditions. The evaluation produces an efficiency factor (0.85 to 1.00). All factors multiply together.

**Why multiplication, not addition:**

Six parts each at 95% efficiency:
- Additive: 1.0 - 6×0.05 = 0.70 total efficiency
- Multiplicative: 0.95⁶ = 0.735 total efficiency

Six parts each at 90%:
- Additive: 1.0 - 6×0.10 = 0.40
- Multiplicative: 0.90⁶ = 0.531

The multiplicative model means:
- No single part dominates (improving one from 0.90→1.00 gives less than improving all from 0.90→0.95)
- Parts optimized together produce compound gains (synergy)
- The gap between "pretty good everywhere" and "excellent everywhere" is meaningful
- A beginner who optimizes one part well but neglects others still loses to someone who's decent at everything

**Target spreads (Monza):**

| Level | Per-Part Efficiency | Product | Lap Time | Gap |
|-------|-------------------|---------|----------|-----|
| Theoretical perfect | 1.00 each | 1.000 | ~78s | 0.0s |
| S-Tier (master) | 0.98 each | 0.886 | ~79s | ~1.0s |
| A-Tier (expert) | 0.96 each | 0.783 | ~80s | ~2.0s |
| B-Tier (good) | 0.93 each | 0.647 | ~82s | ~4.0s |
| C-Tier (learning) | 0.90 each | 0.531 | ~85s | ~7.0s |
| Default (rookie) | 0.85 each | 0.377 | ~88s | ~10.0s |

These numbers align with real F1 data: AWS driver performance metrics show 91-99% extraction = ~3 second spread. F1 vs F2 gap is ~13 seconds (~17% slower). F1 games span ~11 seconds from easiest to hardest AI.

### 3.4 How Efficiency Is Computed (Not Assigned)

The efficiency factor is NOT an arbitrary score. It emerges from the physics:

**Engine map efficiency:** `useful_torque / requested_torque`. If you request 100% torque in a corner where traction limits you to 60%, the extra 40% causes wheelspin (tire wear) but no speed gain. Efficiency = 0.60.

**Gearbox efficiency:** `power_in_current_gear / max_possible_power`. If optimal gear gives 11,000 RPM (torque_curve = 1.0) but you're in a gear that gives 8,000 RPM (torque_curve = 0.78), efficiency = 0.78.

**ERS deploy efficiency:** `speed_gain_from_deployment / speed_gain_if_deployed_optimally`. Deploying 120kW on a straight where you're power-limited: high efficiency. Deploying in a corner where you're traction-limited: near-zero efficiency (energy wasted).

**Brake bias efficiency:** `actual_braking_g / max_possible_braking_g`. Perfect bias achieves 5.5G. Imbalanced bias triggers early lockup on one axle, reducing total to 4.5G. Efficiency = 0.82.

**Suspension efficiency:** `actual_downforce / optimal_downforce`. Ride height -0.6 at 300km/h gives ground_effect_mult = 1.18. Default -0.2 gives 1.06. But -0.9 causes bottoming: mult drops to 0.80×1.27 = 1.02. The optimal is speed-dependent — only adaptive code finds it.

**Cooling efficiency:** `speed_with_actual_cooling / speed_with_optimal_cooling`. Over-cooling adds 8% drag = lower top speed. Under-cooling causes engine temp > 120°C = -2% power per degree. The optimal balance is a narrow band.

**Differential efficiency:** `actual_exit_speed / max_exit_speed`. Over-locked diff in a corner limits rotation (understeer, slower through corner). Under-locked diff on exit causes inside wheelspin (less traction, slower acceleration).

Each of these is computed naturally by the physics engine from the player's actual decision vs the decision that would have produced the best outcome in that specific situation.

---

## 4. The Physics Engine

### 4.1 Simulation Loop (30 Hz)

```
For each tick (dt = 1/30 s):

  For each car:
    1. DRIVER MODEL computes throttle_demand, brake_demand, lateral_target
       (from pre-computed speed profile + racing line)

    2. Call player's ENGINE_MAP(rpm, throttle_demand, engine_temp)
       → torque_pct, fuel_flow_pct

    3. Call player's GEARBOX(rpm, speed, gear, throttle)
       → target_gear

    4. Compute RPM from speed + gear ratio

    5. Call player's FUEL_MIX(fuel_kg, laps_left, position, gap)
       → lambda_value

    6. Call player's SUSPENSION(speed, lat_g, bump, height)
       → ride_height_target

    7. Call player's COOLING(engine_temp, brake_temp, bat_temp, speed)
       → cooling_effort

    8. Call player's ERS_DEPLOY(battery_pct, speed, lap, gap, braking)
       → deploy_kw

    9. COMPUTE FORCES:
       a. Engine power = HP × torque_curve(RPM) × torque_pct × mixture_mult
       b. ERS power = deploy_kw × 1000
       c. Total power = engine_power + ERS_power
       d. Drive force = total_power / velocity                    [F = P/v]
       e. Downforce = 0.5 × ρ × CL × A × v² × ground_effect(ride_height)
       f. Drag = 0.5 × ρ × CD × A × v² × (1 + cooling_drag)
       g. Tire grip = μ × (mass×g + downforce)                   [traction limit]
       h. Lateral force from cornering
       i. Available longitudinal = sqrt(grip² - lateral²)         [traction circle]
       j. Drive force = min(drive_force, available_longitudinal)  [traction-capped]

    10. Call player's BRAKE_BIAS(speed, decel_g, grip_f, grip_r)
        → front_pct (if braking)
        → affects per-axle lockup threshold

    11. Call player's DIFFERENTIAL(phase, speed, lat_g)
        → lock_pct
        → affects torque split, traction on exit

    12. NET FORCE = drive_force - drag - rolling_resistance
        (or -brake_force if braking, capped by traction)

    13. ACCELERATION = net_force / mass

    14. SPEED += acceleration × dt × 3.6

    15. UPDATE STATE:
        a. Engine temp: heat from torque, cool from cooling_effort
        b. Brake temp: heat from braking, cool from airflow
        c. Battery temp: heat from deploy+harvest, cool toward ambient
        d. Tire wear: from slip energy (wheelspin, sliding)
        e. Fuel: consumed this tick based on fuel_flow × lambda
        f. ERS battery: depleted by deploy, charged by harvest
        g. Distance: speed × world_scale × dt

    16. Call player's ERS_HARVEST (if braking)
        → harvest_kw

    17. Call player's STRATEGY(full_state)
        → pit/compound/mode decisions

    18. CODE QUALITY CHECK:
        Roll against reliability score per part
        If glitch: use default output for that part this tick

    19. LOG all part calls (inputs, outputs, status) for viewer
```

### 4.2 Key Physics Equations

**Power to force (speed-limited):**
```
F = P / v
```
Naturally produces correct top speed where drive force = drag.

**Traction circle:**
```
sqrt(F_long² + F_lat²) ≤ μ × (m×g + F_downforce)
```
Can't exceed tire grip. Acceleration, braking, and cornering share the same grip budget.

**Tire force (simplified Pacejka):**
```
F = D × sin(C × atan(B×slip - E×(B×slip - atan(B×slip))))
```
Where D = μ × Fz (peak force), B = stiffness, C = shape, E = curvature.
For the game: simplified to `F = μ × Fz × f(slip)` with a peaked slip curve.

**Aerodynamic forces:**
```
F_down = 0.5 × ρ × CL × A × v² × ground_effect(ride_height)
F_drag = 0.5 × ρ × CD × A × v² × (1 + k_cooling × cooling_effort)
```

**Engine thermal model:**
```
dT/dt = k_heat × torque_pct × (RPM/RPM_ref) - k_cool × cooling_effort × (T - T_ambient)
```

**Fuel consumption:**
```
dm/dt = BSFC × P_engine × lambda_mult
```

**ERS battery:**
```
dE/dt = P_harvest × η_charge - P_deploy / η_discharge
```
Capped at 4 MJ deploy and 2 MJ harvest per lap.

### 4.3 Real F1 Constants

| Parameter | Value | Source |
|-----------|-------|--------|
| Car mass (min) | 798 kg | FIA 2024 regulations |
| ICE power | ~630 kW (850 HP) | Honda/Mercedes published specs |
| MGU-K power | 120 kW (161 HP) | FIA regulation |
| Total power | ~750 kW (~1000 HP) | Combined |
| Tire μ (peak, F1) | 1.4-1.8 | Pirelli data |
| CL (low downforce) | 2.5 | Wind tunnel estimates |
| CL (high downforce) | 4.0 | Wind tunnel estimates |
| CD | 0.85-1.20 | Aero analysis |
| Frontal area | 1.4 m² | Regulation |
| Max braking | 5-6 G | Telemetry data |
| Fuel flow max | 100 kg/hr | FIA regulation |
| Tire radius | 0.33 m | Pirelli spec |
| Air density | 1.225 kg/m³ | Sea level standard |
| Fuel effect on lap time | 0.03 s/kg/lap | Universal F1 figure |
| Pit stop time loss | 22-25 s | FIA timing data |
| DRS speed gain | 10-20 km/h | Track dependent |

---

## 5. Code Quality → Car Reliability

### 5.1 The Mechanic

Complex code has more bugs. This is not an opinion — it's empirically verified (Basili 1986, Nagappan 2006). In NPC Race, this maps directly: complex part functions have more "glitches" — moments where the code produces suboptimal output in edge cases.

A player's car project is analyzed by the engine before racing. The analysis produces a reliability score (0.50 to 1.00). Each tick, each part rolls against its reliability. A failed roll means the part's output is replaced by the default for that tick — the car stutters.

### 5.2 Metrics (Computable from AST, No Dependencies)

| Metric | How It's Computed | Game Effect |
|--------|------------------|-------------|
| Cyclomatic complexity (avg per function) | Count if/elif/for/while/except/and/or + 1 | CC 1-5: no penalty. 6-10: -2% reliability. 11-15: -5%. 16+: -10% |
| Cognitive complexity (max function) | Nesting-aware increments (+1 per flow break, +1 per nesting level) | ≤15: clean. 16-25: -3%. 26+: -8% |
| Lint violations (ruff) | Standard ruff check | 0: +2% bonus. 1-5: neutral. 6-10: -2%. 11+: -5% |
| Function length (max) | Line count | <30: compact bonus +1%. 30-50: neutral. >50: -3% |
| Code duplication | Hash normalized AST subtrees | <5%: clean. 5-15%: -1%. >15%: -3% |
| Type hints present | Check function annotations | Present: +2% bonus |

**Aggregate reliability:**
```
reliability = 1.0
  - cc_penalty
  - cognitive_penalty
  - lint_penalty
  - length_penalty
  - duplication_penalty
  + type_hint_bonus
  + lint_clean_bonus

Clamped to [0.50, 1.00]
```

### 5.3 Glitch Effects

When a part fails its reliability roll, the glitch manifests as a realistic failure mode:

| Part | Glitch | Duration |
|------|--------|----------|
| engine_map | Torque output scaled 0.8-1.0 randomly | 30 ticks (1s) |
| gearbox | Gear change delayed | 10 ticks |
| ers_deploy | Deploy cuts to 0 | 15 ticks |
| brake_bias | Bias drifts ±5 points from target | 20 ticks |
| suspension | Ride height oscillates | 15 ticks |
| cooling | Effort reduced 30% | 20 ticks |
| fuel_mix | Lambda locked at 1.0 | 15 ticks |
| differential | Lock fixed at 50% | 15 ticks |
| strategy | Return ignored | 1 tick |

### 5.4 Why This Works

A player writes a 40-line engine_map with 8 nested if-else branches. CC = 12. Reliability penalty = -5%. Over a 4000-tick race, that's ~200 ticks where the engine stutters. Each stutter costs ~0.01s. Total: ~2 seconds lost to code quality alone.

The fix? Refactor to a lookup table or state machine. CC drops to 3. Penalty drops to 0%. The car runs smoother. The player learned good software engineering by winning a race.

---

## 6. Car Project Structure

### 6.1 Multi-File Format

```
cars/my_team/
├── car.py              # REQUIRED: CAR_NAME, CAR_COLOR, hardware specs
├── powertrain/
│   ├── engine_map.py   # def engine_map(rpm, throttle, temp)
│   ├── gearbox.py      # def gearbox(rpm, speed, gear, throttle)
│   └── fuel_mix.py     # def fuel_mix(fuel_kg, laps_left, pos, gap)
├── hybrid/
│   ├── ers_deploy.py   # def ers_deploy(battery, speed, lap, gap, braking)
│   └── ers_harvest.py  # def ers_harvest(brake_force, battery, temp)
├── chassis/
│   ├── suspension.py   # def suspension(speed, lat_g, bump, height)
│   ├── brake_bias.py   # def brake_bias(speed, decel_g, grip_f, grip_r)
│   ├── cooling.py      # def cooling(eng_temp, brake_temp, bat_temp, speed)
│   └── differential.py # def differential(phase, speed, lat_g)
├── strategy/
│   └── strategy.py     # def strategy(state)
└── helpers/
    └── utils.py        # Shared utilities, lookup tables
```

**Rules:**
- `car.py` must exist with CAR_NAME and CAR_COLOR
- Each part function can be in `car.py` or in its own file
- Missing parts use defaults
- Only imports from within the car directory + Python stdlib
- Total project: no enforced line limit (quality scoring handles complexity naturally)
- Security sandbox: no filesystem, network, or subprocess access

### 6.2 Single-File Format (Backward Compatible)

```
cars/my_car.py
```

All 10 parts as functions in one file. Simpler to start, but code quality scores will be lower for complex single-file builds due to higher per-function complexity in a larger file.

### 6.3 The Default Car (Open Source)

A public template repository. MIT licensed. Full README explaining:
- Every part function with docstrings
- The physics each part connects to
- What "good" vs "bad" decisions look like
- How to test locally
- How to submit

The default car uses all default parts. It finishes races. It's slow. Improving it is the game.

---

## 7. League System

### 7.1 Tiers

| League | Parts Available | Quality Gate | Monza Target |
|--------|----------------|-------------|-------------|
| **F3** | 3 (engine_map, gearbox, strategy) | Must parse, no crashes | ~86-92s |
| **F2** | 6 (+ brakes, suspension, ERS deploy) | Ruff clean | ~82-86s |
| **F1** | All 10 | Ruff clean + CC < 15 | ~79-82s |
| **Championship** | All 10 + multi-file project | Full quality gate (A-grade reliability) | ~78-80s |

### 7.2 Progression

Inspired by iRacing's license system and Gran Turismo's medal structure:

- **F3**: Accessible to anyone learning Python. Only 3 functions to write. Focus on understanding the torque curve and shift points.
- **F2**: Intermediate. Introduces braking physics, suspension dynamics, and energy management. Must write clean code (ruff check passes).
- **F1**: Advanced. All 10 parts interacting. Understanding system-level optimization: how engine_map affects gearbox affects tires. Code complexity limits enforced.
- **Championship**: Expert. Multi-file project structure. Full quality scoring. Competing against other players' cars on the same track.

### 7.3 Calibration Against Real Motorsport

| Our League | Real Analog | Gap to F1 Record |
|-----------|-------------|-------------------|
| Championship S-Tier | Theoretical optimal | +0.0-0.3s |
| Championship A-Tier | F1 pole position | +0.3-1.0s |
| F1 League top | F1 midfield | +1.0-3.0s |
| F2 League top | F2 equivalent | +3.0-7.0s |
| F3 League top | F3 equivalent | +7.0-12.0s |
| Default car | Unoptimized backmarker | +10.0s+ |

Real F1 qualifying at Monza: 1:18.8 (2025 record). Our theoretical best should be achievable but require mastery of all 10 parts plus A-grade code quality. Beating 1:18.8 with perfect code would be the game's ultimate achievement.

---

## 8. Evaluation Pipeline

### 8.1 Submission Flow

```
Player pushes car repo
  → Engine receives webhook / player triggers submission
  → Pull car project
  → STAGE 1: Security scan (bot scanner on all .py files)
  → STAGE 2: Syntax validation (all files parse)
  → STAGE 3: Import validation (no disallowed imports)
  → STAGE 4: Code quality analysis (AST-based metrics)
  → STAGE 5: Compute reliability score
  → STAGE 6: Load into simulation
  → STAGE 7: Run race (qualifying and/or race)
  → STAGE 8: Generate results, replay, narrative
  → STAGE 9: Return results to player
```

### 8.2 Quality Analysis (Internal)

The engine runs quality checks using internal tooling (including paircoder's arch check, gap detection, and validation where applicable). Players never see or interact with this tooling. They see the results:

```
CAR EVALUATION REPORT
=====================
Architecture:  A  (modular structure, functions under 30 lines)
Code Quality:  B+ (CC avg 4.2, 2 minor lint issues)
Reliability:   94%
League:        F1 (all 10 parts detected)
Ready to Race: YES
```

### 8.3 What Players Use Locally

Players can run these checks themselves before submitting:
- `ruff check .` (linting — same rules the engine uses)
- `python -m pytest` (if they write tests for their parts)
- `python -c "from car import *"` (import check)
- Any IDE, AI tool, or development methodology they prefer

The game doesn't prescribe tools. It evaluates results.

---

## 9. The Viewer Experience

### 9.1 Pit Wall Monitor Layout

```
┌──────────────┬────────────────────────────┬─────────────────────────────┐
│              │                            │  YOUR CODE (live terminal)  │
│  TIMING      │     TRACK VIEW             │                             │
│  TOWER       │     (top-down)             │  ▶ gearbox() called         │
│              │                            │    rpm=11200 speed=287      │
│  P1 GOO +0.0│                            │    → gear 7 ✓               │
│  P2 BRI +0.8│                            │                             │
│  P3 YOU +2.1│                            │  ▶ ers_deploy() called      │
│              │                            │    battery=72% speed=310    │
├──────────────┤                            │    → 120kW ✓ (straight)     │
│              │                            │                             │
│  CAR STATUS  │                            │  ▶ brake_bias() called      │
│  (TRON diag) │                            │    speed=312 decel=4.8G     │
│  ┌──┐  ┌──┐ │                            │    → 59% front ⚠ GLITCH     │
│  │▓▓│  │▓▓│ │                            │      (CC=14, reliability    │
│  │ERS████│  │                            │       roll failed)          │
│  │FUEL███│  │                            │                             │
│  │▓▓│  │▓▓│ │                            │  ▶ cooling() called         │
│  DMG: 2%    │                            │    eng=118°C brake=680°C    │
│  REL: 94%   │                            │    → 0.8 ✓                  │
├──────────────┴────────────────────────────┤                             │
│  SPEED ▂▃▅▇▇▅▃▂  TIRE ████░░  ERS ▇▅▃▁  │  Code Grade: B+            │
│  Lap 23/53  1:21.4  Best: 1:20.8         │  Glitches: 3 this lap      │
└──────────────────────────────────────────────────────────────────────────┘
```

### 9.2 Live Code Terminal

The right panel shows your code executing in real-time:
- Each part function highlighted when called
- Input values displayed
- Your code's output shown with ✓ (good) or ⚠ (suboptimal/glitch)
- When a glitch occurs: shows WHY (which quality metric triggered it)
- Scrolling log of the last ~20 calls

### 9.3 TRON Car Diagnostic

A wireframe top-down view of the car:
- 4 tire indicators (color = wear + temperature)
- 4 brake indicators (color = temperature)
- ERS battery bar
- Fuel bar
- Engine temp indicator
- Damage overlay
- Part components PULSE when their function is called
- Components FLASH RED on glitch

---

## 10. Implementation Phases

### Phase 1: Core Physics Engine (Sprints 22-24)

Replace the current parts runner with the multiplicative efficiency model. Implement proper Pacejka tire forces, traction circle, power model with real coupling chain. Verify 10-second spread from default to theoretical perfect on Monza.

**Deliverables:**
- Refactored `parts_runner.py` with real physics coupling
- Simplified Pacejka tire model
- Efficiency computation per part per tick
- Multiplicative aggregation
- Sensitivity test script confirming per-part impact

### Phase 2: Code Quality System (Sprint 25)

Build AST-based quality analyzer. Compute reliability scores. Implement glitch system. Wire into parts runner.

**Deliverables:**
- `engine/code_quality.py` (pure Python AST analysis)
- Reliability score computation
- Per-part glitch system
- Integration with parts runner

### Phase 3: Car Project Loader (Sprint 26)

Multi-file car project support. Directory-based car loading. Security scanning across all files. Quality scoring across all files.

**Deliverables:**
- `engine/car_project_loader.py`
- Extended bot scanner for directories
- Car validation pipeline
- Default car template project

### Phase 4: League System + Viewer (Sprints 27-28)

League definitions with part restrictions. Live code terminal in viewer. TRON car diagnostic. Glitch visualization. Quality grade display.

**Deliverables:**
- `engine/league_system.py`
- `viewer/js/code-terminal.js`
- `viewer/js/car-diagnostic.js`
- Updated dashboard layout

### Phase 5: Race Infrastructure (Sprint 29)

Submission pipeline. Email signup. API key management. Race scheduling. Results delivery. Leaderboards.

**Deliverables:**
- Submission API
- Evaluation pipeline
- Results dashboard
- Leaderboard system

---

## 11. What Makes This Work

### 11.1 The Game Teaches Engineering

To make your car faster, you must understand:
- Torque curves and optimal shift points (mechanical engineering)
- Energy budgets and deployment strategy (electrical engineering)
- Thermodynamics of brakes and engines (thermal engineering)
- Aerodynamic tradeoffs between downforce and drag (aerospace engineering)
- Tire grip limits and traction circles (vehicle dynamics)
- Software reliability and code quality (software engineering)

You can't vibe code your way to victory. You can't just copy someone else's gearbox function because the optimal shift points depend on YOUR engine map, YOUR ERS deployment, YOUR tire condition. The system rewards understanding.

### 11.2 The Game Rewards Good Code

Not just correct code. GOOD code. Clean, modular, well-structured, tested code runs more reliably. A 3-line engine map with a lookup table outperforms a 50-line engine map with nested conditionals — not because it's "better" abstractly, but because the physics simulation literally glitches less when running simpler code.

This is backed by decades of software engineering research. We're not making it up. We're making it a game.

### 11.3 The Game Has Depth

- 10 interacting parts with multiplicative effects
- Per-corner optimization (every track point is different)
- Shifting bottlenecks through the race (tires, fuel, temperature)
- Weather changes requiring adaptation
- Opponent-aware strategy (information asymmetry)
- Code quality affecting reliability
- League progression from 3 parts to 10
- Multiple tracks with different characteristics

The last tenth of a second is the hardest to find. That's where mastery lives.

---

## 12. Calibration Targets

### 12.1 Monza Reference

| Metric | Real F1 (2025) | Game Target |
|--------|---------------|-------------|
| Qualifying record | 1:18.8 | S-Tier theoretical best: ~78s |
| Race pace | 1:20.9 | A-Tier: ~80s |
| Midfield race | 1:22.0 | B-Tier: ~82s |
| Top speed | 355-370 km/h | 340-360 km/h |
| Min corner speed | 68 km/h | 65-80 km/h |
| Braking deceleration | 5-6 G | 5-5.5 G |
| Fuel consumption | 1.9-2.0 kg/lap | 1.8-2.2 kg/lap |

### 12.2 Per-Part Sensitivity Targets

Each part, when optimized vs default, should produce 0.5-1.5s improvement individually. The sum of individual improvements (~6-10s) exceeds the combined improvement (~10s) due to interactions — some positive (synergy), some negative (conflicts).

No single part should account for more than 25% of the total spread.

### 12.3 Code Quality Sensitivity

| Quality Level | Reliability | Glitches per Lap | Time Lost |
|--------------|------------|------------------|-----------|
| A-grade (CC<5, lint clean) | 98%+ | ~0.5 | ~0.1s |
| B-grade (CC 5-10, minor issues) | 94% | ~2 | ~0.5s |
| C-grade (CC 10-15, several issues) | 88% | ~5 | ~1.5s |
| D-grade (CC 15+, many issues) | 80% | ~10 | ~3.0s |

---

## 13. Success Criteria

The system is complete when:

1. ✅ Default car (all default parts) completes a Monza race at ~88s
2. ✅ Fully optimized parts produce ~78s (10-second spread)
3. ✅ Each of 10 parts individually contributes 0.5-1.5s when optimized
4. ✅ Multiplicative interactions visible (sum of parts ≠ total)
5. ✅ A-grade code runs ~3s faster than D-grade code (reliability effect alone)
6. ✅ The viewer shows code executing in real-time with glitch indicators
7. ✅ A player can fork the default car, change one function, submit, and see the difference
8. ✅ A master engineer evaluates the system and confirms the physics is mechanically sound
9. ✅ The sensitivity test produces a clear table showing per-part impact
10. ✅ The interaction test shows at least 3 pairs with measurable coupling
