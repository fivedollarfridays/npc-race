# Getting Started with NPC Race

NPC Race is a competitive coding game where you write Python functions that control an F1 race car. Every function is a real car part — gearbox, cooling system, pit strategy. The physics simulation calls your code 30 times per second. Better engineering decisions make a faster car.

## Prerequisites

- Python 3.11+
- `pip install -e .` (from the repo root)

## Quick Start

```bash
# Create your car project
npcrace init my_car

# Run a race on Monza
npcrace run --car-dir my_car --track monza --laps 1

# Check your results
npcrace submit results.json
```

## Your First Improvement

Run with the default gearbox and note your lap time:

```bash
npcrace run --car-dir my_car --track monza --laps 1
```

Now open `my_car/gearbox.py`. The default shifts at 12,800 RPM — past the engine's peak torque band (10,800-12,500 RPM). Change it:

```python
# Before (default — shifts too late):
if rpm > 12800 and current_gear < 8:

# After (shifts at peak torque):
if rpm > 12200 and current_gear < 8:
```

Run again. Your lap time drops. That is the game — your code makes the car faster.

## How It Works

**10 car parts, each a Python function.** You start with 3 (F3 league):
- `gearbox.py` — when to shift up/down
- `cooling.py` — balance engine temperature vs aerodynamic drag
- `strategy.py` — pit stops, tire compounds, engine modes

As you improve, unlock more parts through league progression (F3 -> F2 -> F1 -> Championship).

**Code quality matters.** Your code is analyzed for complexity. Simpler, cleaner code runs more reliably. Complex code causes random glitches — your gearbox misses a shift, your cooling system stutters. Write clean functions that handle edge cases.

## Submitting Results

```bash
# After a race, submit your results
npcrace submit results.json

# Track your standings
npcrace leaderboard --add results.json
npcrace leaderboard
```

## What's Next

- Read the docstrings in each part file for hints on what "better" means
- Try different tracks: `--track spa`, `--track silverstone`
- Aim for F2: add `suspension.py`, `ers_deploy.py`, `fuel_mix.py`
- Check your code quality: lower complexity = higher reliability = fewer glitches
