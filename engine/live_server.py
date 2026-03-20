"""WebSocket server — streams race frames to viewer in real-time."""

import asyncio
import json

import websockets

from .car_loader import load_all_cars
from .simulation import RaceSim
from .narrative import detect_events
from .commentary import format_events
from .race_report import generate_report
from tracks import get_track
from .track_gen import interpolate_track

DEFAULT_PORT = 8766


async def stream_race(ws, car_dir="cars", track_name="monza", laps=3, seed=42):
    """Run a race and stream frames to WebSocket client."""
    track_data = get_track(track_name)
    track_points = interpolate_track(track_data["control_points"], resolution=500)
    cars = load_all_cars(car_dir)
    sim = RaceSim(
        cars=cars, track_points=track_points, laps=laps, seed=seed,
        track_name=track_name, real_length_m=track_data.get("real_length_m"),
        drs_zones=track_data.get("drs_zones", []),
    )

    # Send init message with track metadata
    init_msg = {
        "type": "init",
        "track": [{"x": round(p[0], 1), "y": round(p[1], 1)} for p in sim.track],
        "track_width": sim.TRACK_WIDTH,
        "track_name": track_name,
        "laps": laps,
        "car_count": len(cars),
        "ticks_per_sec": sim.TICKS_PER_SEC,
    }
    if sim.curvatures:
        init_msg["track_curvatures"] = [round(c, 4) for c in sim.curvatures]
    if sim.headings:
        init_msg["track_headings"] = [round(h, 4) for h in sim.headings]
    await ws.send(json.dumps(init_msg))

    # Stream frames
    paused = False
    speed_mult = 1
    delay = 1.0 / sim.TICKS_PER_SEC

    while not sim.race_over and sim.tick < 36000:
        # Check for client commands (non-blocking)
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=0.001)
            cmd = json.loads(msg)
            if cmd.get("type") == "pause":
                paused = True
            elif cmd.get("type") == "resume":
                paused = False
            elif cmd.get("type") == "speed":
                speed_mult = max(1, min(8, cmd.get("value", 1)))
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed):
            pass

        if paused:
            await asyncio.sleep(0.05)
            continue

        sim.step()

        # Send frame
        if sim.history:
            frame_data = {"type": "frame", "cars": sim.history[-1], "tick": sim.tick}
            await ws.send(json.dumps(frame_data))

        await asyncio.sleep(delay / speed_mult)

    # Send results
    results = sim.get_results()
    replay = sim.export_replay()
    events = detect_events(replay["frames"], sim.TICKS_PER_SEC, results)
    commentary = format_events(events)
    report = generate_report(results, events, commentary, track_name=track_name)

    results_msg = {
        "type": "results",
        "results": results,
        "events": [{"type": e.type, "tick": e.tick, "cars": e.cars, "data": e.data}
                    for e in events],
        "commentary": commentary,
        "race_report": report,
    }
    await ws.send(json.dumps(results_msg))


async def stream_replay(ws, replay_path, speed=1):
    """Stream a saved replay file frame by frame."""
    with open(replay_path) as f:
        replay = json.load(f)

    tps = replay.get("ticks_per_sec", 30)
    init_msg = {
        "type": "init",
        "track": replay["track"],
        "track_width": replay.get("track_width", 50),
        "track_name": replay.get("track_name"),
        "laps": replay.get("laps", 3),
        "car_count": replay.get("car_count", 5),
        "ticks_per_sec": tps,
    }
    if "track_curvatures" in replay:
        init_msg["track_curvatures"] = replay["track_curvatures"]
    if "track_headings" in replay:
        init_msg["track_headings"] = replay["track_headings"]
    await ws.send(json.dumps(init_msg))

    delay = 1.0 / tps
    for i, frame in enumerate(replay["frames"]):
        frame_msg = {"type": "frame", "cars": frame, "tick": i}
        await ws.send(json.dumps(frame_msg))
        await asyncio.sleep(delay / speed)

    results_msg = {"type": "results", "results": replay.get("results", [])}
    if "events" in replay:
        results_msg["events"] = replay["events"]
    if "commentary" in replay:
        results_msg["commentary"] = replay["commentary"]
    if "race_report" in replay:
        results_msg["race_report"] = replay["race_report"]
    await ws.send(json.dumps(results_msg))


async def handler(ws):
    """Handle a WebSocket connection — wait for config then stream."""
    try:
        msg = await asyncio.wait_for(ws.recv(), timeout=10)
        config = json.loads(msg)
    except Exception:
        config = {"mode": "race", "track": "monza", "laps": 3}

    if config.get("mode") == "replay" and config.get("path"):
        await stream_replay(ws, config["path"], config.get("speed", 1))
    else:
        await stream_race(
            ws, car_dir=config.get("car_dir", "cars"),
            track_name=config.get("track", "monza"),
            laps=config.get("laps", 3), seed=config.get("seed", 42))


def start_server(port=DEFAULT_PORT, **kwargs):
    """Start the WebSocket server (blocking)."""
    async def serve():
        async with websockets.serve(handler, "localhost", port):
            print(f"WebSocket server on ws://localhost:{port}")
            await asyncio.Future()  # run forever
    asyncio.run(serve())
