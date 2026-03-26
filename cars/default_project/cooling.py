"""Cooling system — balances engine temperature vs aerodynamic drag.

Called every tick with:
    engine_temp   (float)  engine temperature in Celsius
    brake_temp    (float)  brake temperature in Celsius
    battery_temp  (float)  battery/ERS temperature in Celsius
    speed         (float)  current speed in km/h

Return: cooling effort (float 0.0-1.0).
    0.0 = no cooling (fastest on straights, risk overheating)
    1.0 = maximum cooling (safest, but adds aerodynamic drag)

The default returns 0.48 — safe but draggy.  Values around 0.3-0.5
are usually better than the extremes.  The tradeoff: more cooling
keeps the engine cool but adds drag that slows you on straights.
Less cooling is faster but risks overheating above 120C (which costs
power).

Improvement ideas:
- Return low cooling (0.1-0.2) when engine_temp < 100C
- Ramp up toward 0.6-0.8 as engine_temp approaches 120C
- Target the 108-118C sweet spot for peak efficiency
"""


def cooling(engine_temp, brake_temp, battery_temp, speed):
    return 0.48
