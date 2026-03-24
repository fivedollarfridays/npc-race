# Default Car Project

A starter car for NPC Race. Fork this directory and make it faster.

## Quick Start

```bash
# Run a race with your car
python -m npc_race race cars/default_project/
```

## What's Inside

| File | Part | What It Does |
|------|------|-------------|
| car.py | Metadata | Name, color, stat allocation (100 point budget) |
| cooling.py | Cooling | Balances engine temperature vs aerodynamic drag |
| gearbox.py | Transmission | Decides when to shift up or down |
| strategy.py | Pit Wall | Pit stops, tire compound, engine mode |

The remaining 7 parts use defaults. Unlock them as you move up leagues.

## What to Change First

Pick one file and improve it. The gearbox is a good start:
the default shifts too late (past peak power) and downshifts too early.

Read the docstring in each file for hints on what "better" means.

## Code Quality

Your code is scored on complexity. Simpler code = higher reliability.
High reliability means fewer random glitches during the race.
A clean function that handles edge cases beats a clever one that doesn't.

## Stat Budget

You have 100 points across POWER, GRIP, WEIGHT, AERO, BRAKES.
Edit car.py to reallocate. The default is 20/20/20/20/20.
