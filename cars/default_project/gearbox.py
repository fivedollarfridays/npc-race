"""Gearbox — decides when to shift gears.

Called every tick with:
    rpm        (float)  current engine RPM
    speed      (float)  current speed in km/h
    current_gear (int)  current gear, 1-8
    throttle   (float)  driver throttle input, 0.0-1.0

Return: target gear number (int 1-8).

The engine's torque curve peaks around 10800 RPM and power peaks at
12500 RPM.  The default below shifts at 12800 RPM — past peak power,
so the engine over-revs on every upshift.  Shifting earlier (e.g.
11000-12200 RPM) keeps the engine in its torque band and can drop your
lap time by ~1 second on a track like Monza.

Improvement ideas:
- Tune the upshift threshold to the torque peak (~11000-12200 RPM)
- Use speed to anticipate braking zones and downshift earlier
- Vary thresholds per gear (lower gears can shift sooner)
"""


def gearbox(rpm, speed, current_gear, throttle):
    if rpm > 12800 and current_gear < 8:
        return current_gear + 1
    if rpm < 6200 and current_gear > 1:
        return current_gear - 1
    return current_gear
