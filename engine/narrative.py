"""Race event detection — scans replay frames for narrative events."""

BATTLE_GAP_THRESHOLD = 1.0  # seconds
BATTLE_MIN_DURATION = 90    # frames (3s at 30fps)


class RaceEvent:
    """A detected race event."""
    __slots__ = ("type", "tick", "cars", "data")

    def __init__(self, event_type, tick, cars, data=None):
        self.type = event_type
        self.tick = tick
        self.cars = cars
        self.data = data or {}


def detect_events(replay_frames, ticks_per_sec=30, results=None):
    """Scan replay frames and return chronological list of events."""
    events = []
    events.extend(detect_overtakes(replay_frames))
    events.extend(detect_battles(replay_frames, ticks_per_sec))
    events.extend(detect_incidents(replay_frames))
    events.extend(detect_pit_stops(replay_frames))
    if results:
        events.extend(detect_fastest_laps(results))
    events.sort(key=lambda e: e.tick)
    return events


def detect_overtakes(frames):
    """Find position swaps between adjacent cars."""
    events = []
    if len(frames) < 2:
        return events
    for tick in range(1, len(frames)):
        prev_pos = {c["name"]: c["position"] for c in frames[tick - 1]}
        curr_pos = {c["name"]: c["position"] for c in frames[tick]}
        for name, pos in curr_pos.items():
            old = prev_pos.get(name, pos)
            if pos < old:  # gained position
                passed = [n for n, p in prev_pos.items() if p == pos and n != name]
                if passed:
                    events.append(RaceEvent("OVERTAKE", tick, [name, passed[0]],
                                            {"position": pos, "lap": frames[tick][0].get("lap", 0)}))
    return events


def detect_battles(frames, tps):
    """Find sustained close battles between car pairs."""
    events = []
    if len(frames) < BATTLE_MIN_DURATION:
        return events
    pairs = {}  # (name_a, name_b) -> consecutive_frames
    for tick, frame in enumerate(frames):
        by_pos = sorted(frame, key=lambda c: c["position"])
        active = set()
        for i in range(len(by_pos) - 1):
            a, b = by_pos[i], by_pos[i + 1]
            gap = abs(b.get("gap_ahead_s", 99))
            pair = (a["name"], b["name"])
            if gap <= BATTLE_GAP_THRESHOLD:
                pairs[pair] = pairs.get(pair, 0) + 1
                active.add(pair)
                if pairs[pair] == BATTLE_MIN_DURATION:
                    events.append(RaceEvent("BATTLE", tick, [a["name"], b["name"]],
                                            {"gap": gap, "duration_frames": BATTLE_MIN_DURATION}))
            else:
                pairs[pair] = 0
        for p in list(pairs):
            if p not in active:
                pairs[p] = 0
    return events


def detect_incidents(frames):
    """Find spins, safety cars."""
    events = []
    if len(frames) < 2:
        return events
    for tick in range(1, len(frames)):
        prev = {c["name"]: c for c in frames[tick - 1]}
        for car in frames[tick]:
            name = car["name"]
            p = prev.get(name, {})
            if car.get("in_spin") and not p.get("in_spin"):
                events.append(RaceEvent("SPIN", tick, [name]))
            if car.get("safety_car") and not p.get("safety_car"):
                events.append(RaceEvent("SAFETY_CAR", tick, [name], {"reason": "incident"}))
    return events


def detect_pit_stops(frames):
    """Find pit stop entries."""
    events = []
    if len(frames) < 2:
        return events
    for tick in range(1, len(frames)):
        prev = {c["name"]: c for c in frames[tick - 1]}
        for car in frames[tick]:
            name = car["name"]
            p = prev.get(name, {})
            if car.get("pit_status") != "racing" and p.get("pit_status") == "racing":
                events.append(RaceEvent("PIT_STOP", tick, [name],
                                        {"compound": car.get("tire_compound", "medium")}))
    return events


def detect_fastest_laps(results):
    """Find fastest lap from results."""
    valid = [(r["name"], r["best_lap_s"]) for r in results
             if r.get("best_lap_s") is not None]
    if not valid:
        return []
    fastest = min(valid, key=lambda x: x[1])
    return [RaceEvent("FASTEST_LAP", 0, [fastest[0]], {"time": fastest[1]})]
