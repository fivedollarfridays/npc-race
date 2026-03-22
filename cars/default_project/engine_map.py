"""Engine map — controls torque and fuel delivery.

Receives: rpm (float), throttle_demand (float 0-1), engine_temp (float C)
Returns: (torque_pct: float 0-1, fuel_flow_pct: float 0-1)

The default requests full power always. Better code would:
- Reduce torque in corners to prevent wheelspin and tire wear
- Derate when engine_temp > 115C to stay in the thermal sweet spot
- Match fuel flow to torque to avoid wasting fuel
"""


def engine_map(rpm, throttle_demand, engine_temp):
    return (1.0, 1.0)
