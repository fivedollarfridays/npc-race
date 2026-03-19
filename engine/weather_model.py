"""Weather state machine with grip/wear penalties and forecast system."""
import random

# Weather states
DRY = "dry"
DAMP = "damp"
WET = "wet"
HEAVY_RAIN = "heavy_rain"

# Wetness values per state
STATE_WETNESS = {DRY: 0.0, DAMP: 0.2, WET: 0.5, HEAVY_RAIN: 0.8}

# Transition probabilities per lap: state -> [(target, probability), ...]
TRANSITIONS = {
    DRY: [(DAMP, 0.08)],
    DAMP: [(WET, 0.15), (DRY, 0.20)],
    WET: [(HEAVY_RAIN, 0.10), (DAMP, 0.15)],
    HEAVY_RAIN: [(WET, 0.20)],
}

DRY_COMPOUNDS = {"soft", "medium", "hard"}


def create_weather_state(initial: str = DRY) -> dict:
    """Return initial weather state dict."""
    return {
        "state": initial,
        "wetness": STATE_WETNESS.get(initial, 0.0),
        "lap_count": 0,
    }


def update_weather(weather_state: dict, rng) -> dict:
    """Advance weather by one lap with probabilistic transitions."""
    current = weather_state["state"]
    new_state = current
    transitioned = False
    for t_state, prob in TRANSITIONS.get(current, []):
        if rng.random() < prob:
            new_state = t_state
            transitioned = True
            break
    target_wetness = STATE_WETNESS[new_state]
    old_wetness = weather_state["wetness"]
    rate = 0.7 if transitioned else 0.5
    wetness = old_wetness + (target_wetness - old_wetness) * rate
    return {
        "state": new_state,
        "wetness": round(wetness, 4),
        "lap_count": weather_state["lap_count"] + 1,
    }


def get_wetness_grip_mult(wetness: float, compound: str) -> float:
    """Return grip multiplier [0.0-1.0] based on wetness and compound."""
    if compound in DRY_COMPOUNDS:
        return max(0.0, min(1.0, 1.0 - wetness * 0.6))
    if compound == "intermediate":
        return max(0.0, min(1.0, 1.0 - abs(wetness - 0.45) * 0.8))
    # wet compound
    return max(0.0, min(1.0, 1.0 - max(0.0, 0.6 - wetness) * 1.0))


def get_wetness_wear_mult(wetness: float, compound: str) -> float:
    """Return wear multiplier based on wetness and compound mismatch."""
    if compound in DRY_COMPOUNDS:
        # Dry on wet: aquaplaning stress
        return 1.0 + wetness * 1.0
    if compound == "intermediate":
        # Penalty when far from optimal range (0.3-0.6)
        dist = max(0.0, abs(wetness - 0.45) - 0.15)
        return 1.0 + dist * 0.8
    # wet compound on dry: overheating
    return 1.0 + max(0.0, 0.6 - wetness) * 0.8


def generate_forecast(
    weather_state: dict, laps_ahead: int, rng
) -> list[tuple[int, float]]:
    """Generate forecast with noise: list of (lap, predicted_wetness).

    Uses a forked RNG so forecast generation doesn't affect race outcomes.
    """
    forecast_rng = random.Random(rng.randint(0, 2**32))
    forecast = []
    ws = dict(weather_state)
    base_lap = ws["lap_count"]
    for i in range(1, laps_ahead + 1):
        ws = update_weather(ws, forecast_rng)
        noise = forecast_rng.uniform(-0.1, 0.1)
        predicted = max(0.0, min(1.0, ws["wetness"] + noise))
        forecast.append((base_lap + i, round(predicted, 4)))
    return forecast


def get_optimal_compound(wetness: float) -> str:
    """Return best compound name for current wetness level."""
    if wetness < 0.25:
        return "medium"
    if wetness < 0.55:
        return "intermediate"
    return "wet"
