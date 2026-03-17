# Adaptive Intelligence — Spec

> NPC Race: From static strategies to organically improving AI racers

---

## Problem

Every car strategy is a pure function — same inputs, same outputs, forever. BrickHouse loses every race because its 2-stop strategy fires on 2-lap races. No car adapts to opponents, track conditions, or past performance. The game has no progression, no emergent behavior, and no reason to race twice.

## Vision

Four layers of intelligence, each building on the last. A player should be able to write a Level 1 car and compete, but the ceiling goes all the way to neural networks. The seed cars should demonstrate each level so players see what's possible.

---

## Level 1 — Reactive Adaptation (within a single race)

### What it is

Strategies that dynamically adjust based on race conditions — not just following a fixed plan. The strategy function uses the full state dict to make contextual decisions in real-time.

### What changes

No engine changes. This is purely better strategy code in the car files.

### Key behaviors

**Adaptive pit timing:**
```python
# Don't pit on fixed lap %, pit based on conditions
if tire_wear > 0.7 and gap_ahead_s > 25:
    # Tires shot, big gap to cover pit time — pit now
    pit_request = True
elif tire_wear > 0.85:
    # Emergency pit regardless
    pit_request = True
```

**Position-aware engine modes:**
```python
if position == 1 and gap_behind_s > 3.0:
    engine_mode = "conserve"  # Protect lead, save fuel
elif position > 1 and gap_ahead_s < 2.0:
    engine_mode = "push"  # Close enough to attack
```

**Defensive/offensive lateral:**
```python
if gap_behind_s < 1.0 and curvature < 0.05:
    # Car right behind on a straight — block the inside
    lateral_target = nearby_cars[0]["lateral"]
elif curvature > 0.1:
    # Corner — take the racing line
    lateral_target = -0.8  # Inside line
```

**Tire compound selection based on remaining laps:**
```python
laps_remaining = total_laps - lap
if laps_remaining < 15:
    compound = "soft"  # Sprint to the end
elif laps_remaining < 30:
    compound = "medium"
else:
    compound = "hard"  # Long stint ahead
```

### Seed car upgrades

| Car | Current flaw | Level 1 fix |
|-----|-------------|-------------|
| BrickHouse | Pits at fixed 25%/60% on 2-lap races | Pit only when tire_wear > 0.7 AND enough laps to recover time |
| SlipStream | Always pits at 55% | Pit when gap allows, or undercut when car ahead pits |
| GooseLoose | Fixed push/conserve split | Switch modes based on position and gap |
| GlassCanon | Never pits (even with dead tires) | Emergency pit if grip cliff hits mid-race |
| Silky | Fixed inside line | Adaptive: inside in corners, block on straights when defending |

### Complexity: 30 Cx
### Files: `cars/*.py` (5 files)
### Dependencies: None (uses existing state fields)

---

## Level 2 — Cross-Race Learning (between races)

### What it is

Strategies can persist data to a JSON file between races. A car remembers what worked and adjusts. This is the "team notebook" — recording pit windows, tire degradation curves, competitor behavior, and optimal racing lines per track.

### What changes

**Engine:**
- Add `car_data_dir` parameter to `run_race` — directory where cars can read/write JSON
- Pass `data_file` path in strategy state: `state["data_file"] = "cars/data/brickhouse.json"`
- Strategy can call `load_data()` / `save_data()` helper functions (provided in car_template.py)

**Security:**
- `bot_scanner` allows `json` import (add to ALLOWED_IMPORTS)
- `bot_scanner` allows `open()` ONLY for files in the car's own data directory (path validation)
- File size limit: 1MB per car data file
- No network access, no subprocess, no arbitrary file paths

**Strategy state additions:**
```python
state["data_file"] = "/path/to/cars/data/carname.json"  # Read/write path
state["track_name"] = "monaco"  # Already exists
state["race_number"] = 3  # Which race in a series (new)
```

### Key behaviors

**Track-specific pit windows:**
```python
data = load_data(state["data_file"])
track = state["track_name"]

# Get best pit lap from history on this track
best_pit_lap = data.get(track, {}).get("best_pit_lap", None)
if best_pit_lap and lap == best_pit_lap:
    pit_request = True

# After race, record what worked
if state["finished"]:
    data[track] = {"best_pit_lap": actual_pit_lap, "position": position}
    save_data(state["data_file"], data)
```

**Opponent profiling:**
```python
# Track how each opponent behaves
for car in nearby_cars:
    opponent = data.get("opponents", {}).get(car["name"], {})
    # Record: does this car tend to pit early? Block on straights?
    opponent["avg_speed"] = running_average(opponent.get("avg_speed", 0), car["speed"])
```

**Tire degradation modeling:**
```python
# Record tire wear curve per track
wear_at_lap = data.get(track, {}).get("wear_curve", [])
wear_at_lap.append({"lap": lap, "wear": tire_wear, "compound": tire_compound})
# Use this to predict when to pit on next race
```

### Data file format
```json
{
  "monaco": {
    "best_pit_lap": 18,
    "best_compound_order": ["soft", "hard"],
    "avg_lap_time": 76.2,
    "wear_curve": [{"lap": 1, "wear": 0.02}, {"lap": 2, "wear": 0.05}]
  },
  "opponents": {
    "Silky": {"avg_speed": 165, "tends_to_pit_early": true},
    "GlassCanon": {"avg_speed": 180, "never_pits": true}
  },
  "races_completed": 12,
  "total_wins": 3
}
```

### Helper functions (provided in car_template.py)
```python
import json

def load_data(path):
    """Load car's persistent data. Returns {} if no data yet."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(path, data):
    """Save car's persistent data."""
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
```

### Seed car upgrades

| Car | Level 2 behavior |
|-----|-----------------|
| BrickHouse | Records optimal pit laps per track, adjusts strategy each race |
| SlipStream | Profiles opponents' lateral tendencies, positions for draft accordingly |
| GooseLoose | Tracks fuel consumption per track, calibrates engine mode per stint |
| Silky | Records wear curves per compound per track, optimizes compound choice |
| GlassCanon | Monitors if 0-stop works per track, switches to 1-stop if data shows it loses |

### Tournament mode (new CLI command)
```bash
npcrace tournament --tracks monaco,monza,silverstone --races 5
```
Runs multiple races in sequence. Cars accumulate data between races. Points: 25/18/15/12/10 per race. Championship standings after all races.

### Complexity: 80 Cx
### Files: `engine/simulation.py`, `engine/race_runner.py`, `security/bot_scanner.py`, `car_template.py`, `cli/`, `cars/*.py`, `cars/data/` (new dir)
### Dependencies: Level 1

---

## Level 3 — Evolutionary Strategies (genetic algorithms)

### What it is

A parameter-driven strategy where the "genes" are numeric constants (pit threshold, throttle curve, lateral aggression, etc.). A genetic algorithm breeds successive generations — mutating winners, crossing over traits, culling losers. Over 50-100 generations, strategies evolve toward optimal.

### What changes

**New module: `engine/evolution.py`**
- Genome: dictionary of float parameters that a strategy template reads
- Population: N cars (20-50) per generation
- Fitness: race position → points, plus bonuses for finishing, efficient fuel use
- Selection: tournament selection (pick 3 random, keep best)
- Crossover: uniform crossover of genome parameters
- Mutation: gaussian noise on 10-20% of parameters per generation
- Elitism: top 2 carry forward unchanged

**New strategy template: `car_template_evolved.py`**
```python
# Genome — these values are injected by the evolution engine
GENOME = {
    "pit_wear_threshold": 0.72,
    "push_position_threshold": 3,
    "conserve_gap_threshold": 4.5,
    "corner_throttle_factor": 0.65,
    "lateral_aggression": 0.8,
    "compound_switch_lap_pct": 0.45,
    "boost_lap_threshold": 0.85,
}

def strategy(state):
    g = GENOME

    # Pit when wear exceeds evolved threshold
    pit_request = state["tire_wear"] > g["pit_wear_threshold"]

    # Engine mode based on evolved position threshold
    if state["position"] > g["push_position_threshold"]:
        engine_mode = "push"
    elif state["gap_behind_s"] > g["conserve_gap_threshold"]:
        engine_mode = "conserve"
    else:
        engine_mode = "standard"

    # Corner throttle from evolved factor
    throttle = g["corner_throttle_factor"] if state["curvature"] > 0.1 else 1.0

    # ... etc
```

**New CLI command:**
```bash
npcrace evolve --generations 50 --population 30 --track monaco --laps 10
```
Outputs: `evolved_champion.py` — the best-performing car after N generations.

### Evolution pipeline

```
Generation 0: Random genomes (30 cars)
     ↓
Race all 30 on target track(s) → fitness scores
     ↓
Select top 50% → crossover pairs → mutate offspring
     ↓
Generation 1: 30 cars (15 offspring + 13 mutants + 2 elites)
     ↓
Repeat 50-100x
     ↓
Output: champion genome + convergence plot
```

### Fitness function
```python
def compute_fitness(result, race_data):
    position_points = {1: 100, 2: 80, 3: 65, 4: 50, 5: 40}
    fitness = position_points.get(result["position"], 30)

    # Bonus for finishing
    if result["finished"]:
        fitness += 20

    # Bonus for fuel efficiency (finished with fuel remaining)
    fitness += race_data["final_fuel_pct"] * 10

    # Bonus for fewer pit stops (strategy efficiency)
    fitness -= race_data["pit_stops"] * 5

    return fitness
```

### Visualization
- Convergence chart: best/avg/worst fitness per generation
- Gene heatmap: which parameters converged vs stayed diverse
- Race replay of the champion vs generation-0 cars

### Complexity: 100 Cx
### Files: `engine/evolution.py` (new), `car_template_evolved.py` (new), `cli/commands.py`, `scripts/evolve.py`
### Dependencies: Level 1 (reactive strategies as base template)

---

## Level 4 — Neural Network Strategies (ML-based)

### What it is

A small neural network replaces the if/else strategy logic. The network takes the state vector as input and outputs continuous action values. Trained via reinforcement learning (self-play) or imitation learning (from evolved champions).

### What changes

**New module: `engine/neural_strategy.py`**
- Minimal NN implementation in pure Python (no PyTorch/TensorFlow — stdlib only)
- Architecture: 2-layer MLP (state_dim → 32 → 16 → action_dim)
- Activations: tanh for hidden layers, sigmoid/tanh for outputs
- Weights stored as flat numpy-free arrays (lists of lists)

**State vector (input, ~20 floats):**
```python
[
    speed / 300,                    # Normalized speed
    position / total_cars,          # Relative position
    lap / total_laps,               # Race progress
    tire_wear,                      # 0-1
    fuel_pct,                       # 0-1
    curvature * 10,                 # Scaled curvature
    gap_ahead_s / 10,              # Normalized gap
    gap_behind_s / 10,
    tire_age_laps / 20,
    float(pit_stops) / 3,
    # One-hot compound: soft, medium, hard
    float(compound == "soft"),
    float(compound == "medium"),
    float(compound == "hard"),
    # Nearby car features (top 2)
    nearby[0].distance / 50,
    nearby[0].speed / 300,
    nearby[1].distance / 50,
    nearby[1].speed / 300,
    lateral,
    # Track context
    float(engine_mode == "push"),
    float(engine_mode == "conserve"),
]
```

**Action vector (output, ~6 floats):**
```python
[
    throttle,           # sigmoid → 0-1
    lateral_target,     # tanh → -1 to 1
    pit_probability,    # sigmoid → 0-1, pit if > 0.5
    compound_logits[3], # softmax → soft/medium/hard
    engine_mode_logits[3],  # softmax → push/standard/conserve
]
```

**Pure Python neural network (no dependencies):**
```python
import math

def sigmoid(x):
    return 1 / (1 + math.exp(-max(-500, min(500, x))))

def tanh(x):
    return math.tanh(max(-500, min(500, x)))

def forward(weights, biases, inputs):
    """2-layer MLP forward pass."""
    # Hidden layer 1
    h1 = [tanh(sum(w * x for w, x in zip(row, inputs)) + b)
           for row, b in zip(weights[0], biases[0])]
    # Hidden layer 2
    h2 = [tanh(sum(w * x for w, x in zip(row, h1)) + b)
           for row, b in zip(weights[1], biases[1])]
    # Output layer
    out = [sum(w * x for w, x in zip(row, h2)) + b
           for row, b in zip(weights[2], biases[2])]
    return out
```

**Training approaches:**

**A. Reinforcement learning (self-play):**
- Run races with random-weight networks
- Reward = fitness function from Level 3
- Update weights via simple evolution strategy (ES) — no backprop needed
  - ES is gradient-free: perturb weights, measure fitness, move toward better perturbations
  - This is actually Level 3's genetic algorithm applied to NN weights
- 500-1000 generations to converge

**B. Imitation learning (from Level 3 champions):**
- Run 100 races with the evolved champion from Level 3
- Record (state, action) pairs at every tick
- Train NN to predict the champion's actions from states
- Supervised learning via gradient descent (pure Python implementation)
- Results in a smooth, continuous version of the evolved strategy

**C. Hybrid:**
- Bootstrap with imitation learning (fast initial competence)
- Fine-tune with self-play RL (discover novel strategies)

### Car file format for neural strategies
```python
"""NeuralRacer — trained on 500 generations of Monaco self-play."""

CAR_NAME = "NeuralRacer"
CAR_COLOR = "#9900ff"
POWER = 25
GRIP = 25
WEIGHT = 15
AERO = 20
BRAKES = 15

# Weights exported from training
WEIGHTS = [
    [[0.12, -0.34, ...], ...],  # Layer 1: 20x32
    [[0.05, 0.78, ...], ...],   # Layer 2: 32x16
    [[0.91, -0.22, ...], ...],  # Layer 3: 16x6
]
BIASES = [
    [0.01, -0.02, ...],  # Layer 1: 32
    [0.03, 0.01, ...],   # Layer 2: 16
    [0.00, 0.05, ...],   # Layer 3: 6
]

def strategy(state):
    inputs = encode_state(state)  # State → 20-float vector
    outputs = forward(WEIGHTS, BIASES, inputs)
    return decode_actions(outputs)  # 6-float vector → decision dict
```

### CLI commands
```bash
npcrace train --method evolve --generations 500 --track monaco
npcrace train --method imitate --champion cars/evolved_champion.py --episodes 100
npcrace train --method hybrid --bootstrap cars/evolved_champion.py --finetune 200
```

### Complexity: 120 Cx
### Files: `engine/neural_strategy.py` (new), `engine/training.py` (new), `scripts/train.py` (new), `cli/commands.py`
### Dependencies: Level 3 (for imitation learning source), Level 1 (for state encoding)

---

## Implementation Roadmap

| Sprint | Level | Focus | Tasks | Cx |
|--------|-------|-------|-------|----|
| 4 | 1 | Reactive seed cars | Rewrite 5 cars with adaptive logic | 30 |
| 4 | 2 | Cross-race learning | Data persistence, tournament mode, scanner update | 80 |
| 5 | 3 | Genetic evolution | Evolution engine, genome template, evolve CLI | 100 |
| 6 | 4 | Neural strategies | Pure-Python NN, training loop, train CLI | 120 |
| **Total** | | | | **330** |

### Sprint 4 scope (Levels 1+2): 110 Cx
```
T4.1  Reactive seed cars (Level 1)                   30 Cx
T4.2  Data persistence system (json read/write)       25 Cx
T4.3  Scanner update (allow json import, path gate)   15 Cx
T4.4  Tournament mode CLI                             25 Cx
T4.5  Learning seed cars (Level 2)                    30 Cx
T4.6  Integration gate                                15 Cx
```

### Sprint 5 scope (Level 3): 100 Cx
```
T5.1  Evolution engine (selection, crossover, mutation)  40 Cx
T5.2  Genome strategy template                           20 Cx
T5.3  Evolve CLI command + convergence output            25 Cx
T5.4  Evolved champion seed car                          15 Cx
```

### Sprint 6 scope (Level 4): 120 Cx
```
T6.1  Pure-Python neural network module                  30 Cx
T6.2  State encoder / action decoder                     20 Cx
T6.3  ES-based training loop                             30 Cx
T6.4  Imitation learning from champion                   25 Cx
T6.5  Train CLI + neural seed car                        15 Cx
```

---

## Design Principles

1. **No external dependencies.** The neural network is pure Python. No numpy, no torch, no tensorflow. This keeps the game portable and the car files self-contained.

2. **Strategies are just Python files.** Whether a car uses if/else, JSON history, evolved parameters, or neural network weights — it's all a `strategy(state) → dict` function in a `.py` file. The engine doesn't care how decisions are made.

3. **The ceiling is high but the floor is low.** A new player can write `return {"throttle": 1.0}` and race. An advanced player can evolve a neural network. Both compete on the same track.

4. **Cars carry their intelligence.** A neural car file contains its weights inline. An evolved car contains its genome. A learning car has a JSON sidecar. You can email someone a `.py` file and they can race it.

5. **The game teaches F1.** Each level teaches something:
   - Level 1: Race strategy (when to push, when to conserve)
   - Level 2: Data analysis (track your performance, study opponents)
   - Level 3: Optimization (what parameters matter? how do they interact?)
   - Level 4: Machine learning (state representation, reward shaping, generalization)
