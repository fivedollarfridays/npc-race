"""
Replay recording and export for NPC Race.

Contains functions for recording animation frames, computing race results,
and exporting replay data as JSON-compatible dicts.
"""

import bisect
import math


def get_track_pos(distance, track, distances, track_length):
    """Get x,y position on track from distance traveled."""
    d = distance % track_length
    if d < 0:
        d += track_length
    i = bisect.bisect_right(distances, d) - 1
    i = max(0, min(i, len(distances) - 2))
    seg_len = distances[i + 1] - distances[i]
    t = (d - distances[i]) / seg_len if seg_len > 0.001 else 0
    x = track[i][0] + t * (track[i + 1][0] - track[i][0])
    y = track[i][1] + t * (track[i + 1][1] - track[i][1])
    return x, y, i


def _compute_positions(states):
    """Return sorted positions (1st, 2nd, etc.)"""
    ranked = sorted(states, key=lambda s: (
        -s["lap"],
        -s["distance"],
        s["finish_tick"] or float("inf")
    ))
    positions = {}
    for pos, s in enumerate(ranked):
        positions[s["car_idx"]] = pos + 1
    return positions


def record_frame(states, positions, track, distances, track_length,
                 track_width, tick=0, ticks_per_sec=30):
    """Record one animation frame for replay."""
    frame = []
    for state in states:
        x, y, seg = get_track_pos(
            state["distance"], track, distances, track_length
        )
        # Lateral offset
        if seg < len(track) - 1:
            dx = track[seg + 1][0] - track[seg][0]
            dy = track[seg + 1][1] - track[seg][1]
        else:
            dx = track[0][0] - track[seg][0]
            dy = track[0][1] - track[seg][1]
        length = math.sqrt(dx * dx + dy * dy) + 0.001
        nx, ny = -dy / length, dx / length
        lat_offset = state["lateral"] * track_width * 0.4
        x += nx * lat_offset
        y += ny * lat_offset

        max_fuel = max(state.get("max_fuel_kg", 1), 0.001)
        fuel_pct = round(state.get("fuel_kg", 0) / max_fuel, 2)
        pit_state = state.get("pit_state", {})

        frame.append({
            "x": round(x, 1),
            "y": round(y, 1),
            "name": state["name"],
            "color": state["color"],
            "speed": round(state["speed"], 1),
            "lap": state["lap"],
            "position": positions[state["car_idx"]],
            "tire_wear": round(state["tire_wear"], 2),
            "boost": state["boost_active"] > 0,
            "finished": state["finished"],
            "seg": seg,
            "tire_compound": state.get("tire_compound", "medium"),
            "fuel_pct": fuel_pct,
            "pit_status": pit_state.get("status", "racing")
            if isinstance(pit_state, dict) else "racing",
            "engine_mode": state.get("engine_mode", "standard"),
            "lateral": round(state.get("lateral", 0.0), 2),
            "tire_temp": round(state.get("tire_temp", 20.0), 1),
            "drs_active": bool(state.get("drs_active", False)),
            "elapsed_s": round(tick / ticks_per_sec, 2),
            "gap_ahead_s": round(state.get("_gap_ahead_s", 0.0), 3),
            "current_sector": state.get("_timing", {}).get(
                "current_sector", 0),
            "in_dirty_air": bool(state.get("_in_dirty_air", False)),
            "gap_behind_s": round(state.get("_gap_behind_s", 0.0), 3),
            "last_lap_time": state.get("_last_lap_time"),
            "best_lap_s": state.get("_best_lap_s"),
            "tire_age_laps": state.get("tire_age_laps", 0),
            "pit_stops": state.get("pit_state", {}).get("pit_stops", 0),
            "dirty_air_factor": round(state.get("_dirty_air_grip", 1.0), 3),
            "last_sector_time": state.get("_last_sector_time"),
            "last_sector_idx": state.get("_last_sector_idx"),
            "damage": round(state.get("damage", {}).get("damage", 0.0), 3),
            "in_spin": state.get("spin_recovery", 0) > 0,
            "safety_car": bool(state.get("_safety_car", False)),
            "track_wetness": round(state.get("_track_wetness", 0.0), 3),
            "ers_energy": round(state.get("ers", {}).get("energy", 4.0), 2),
            "brake_temp": round(state.get("brake_state", {}).get("temp", 20.0), 1),
        })

    return frame


def get_results(states, num_cars, timings=None, ticks_per_sec=30):
    """Get final race results with optional timing enrichment."""
    positions = _compute_positions(states)
    results = []
    for state in states:
        r = {
            "name": state["name"],
            "color": state["color"],
            "position": positions[state["car_idx"]],
            "finish_tick": state["finish_tick"],
            "finished": state["finished"],
        }
        ft = state.get("finish_tick")
        r["total_time_s"] = round(ft / ticks_per_sec, 2) if ft else None
        ps = state.get("pit_state", {})
        r["pit_stops"] = ps.get("pit_stops", 0) if isinstance(ps, dict) else 0
        if timings and state["name"] in timings:
            ct = timings[state["name"]]
            r["best_lap_s"] = ct.best_lap
            r["lap_times"] = [round(t, 3) for t in ct.lap_times]
        else:
            r["best_lap_s"] = None
            r["lap_times"] = []
        results.append(r)
    results.sort(key=lambda r: r["position"])
    return results


def export_replay(track, track_width, track_name, laps, ticks_per_sec,
                  history, states, num_cars, track_curvatures=None,
                  track_headings=None, timings=None):
    """Export replay data as JSON-compatible dict."""
    track_xy = [{"x": round(p[0], 1), "y": round(p[1], 1)} for p in track]
    replay = {
        "track": track_xy,
        "track_width": track_width,
        "track_name": track_name,
        "laps": laps,
        "ticks_per_sec": ticks_per_sec,
        "frames": history,
        "results": get_results(states, num_cars, timings, ticks_per_sec),
        "car_count": num_cars,
    }
    if track_curvatures is not None:
        replay["track_curvatures"] = [round(c, 4) for c in track_curvatures]
    if track_headings is not None:
        replay["track_headings"] = [round(h, 4) for h in track_headings]
    return replay
