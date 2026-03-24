"""Gearbox — decides when to shift gears.

Receives: rpm (float), speed (float km/h), current_gear (int 1-8),
          throttle (float 0-1)
Returns: target_gear (int 1-8)

The torque curve peaks around 10800 rpm and power peaks at 12500.
Shifting too late (past peak power) wastes time revving.
Shifting too early (below peak torque) loses acceleration.
Better code would shift at rpm thresholds tuned to the torque curve
and use speed to anticipate downshifts for braking zones.
"""


def gearbox(rpm, speed, current_gear, throttle):
    if rpm > 12800 and current_gear < 8:
        return current_gear + 1
    if rpm < 6200 and current_gear > 1:
        return current_gear - 1
    return current_gear
