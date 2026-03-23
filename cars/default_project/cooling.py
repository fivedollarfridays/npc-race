"""Cooling system — balances engine temperature vs aerodynamic drag.

Receives: engine_temp (float C), brake_temp (float C), battery_temp (float C), speed (float km/h)
Returns: cooling_effort (float 0.0-1.0)

The default uses fixed cooling. Better code would:
- Use minimal cooling when engine is cool (less drag = faster straights)
- Ramp up cooling when engine approaches 120C (overheating costs power)
- Target the 108-118C sweet spot where the engine runs most efficiently
"""


def cooling(engine_temp, brake_temp, battery_temp, speed):
    return 0.48
