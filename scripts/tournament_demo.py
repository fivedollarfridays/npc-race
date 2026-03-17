"""Tournament demo script for Sprint 4 adaptive intelligence.

Runs a 3-race Monaco tournament then a 5-race Monza tournament,
demonstrating cross-race learning in the seed cars.

Usage:
    python scripts/tournament_demo.py
"""

import os
import subprocess
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_tournament(tracks, races, laps=3, data_dir="cars/data", output_dir="demo_output"):
    """Run a tournament via the CLI and print results."""
    cmd = [
        sys.executable, "-m", "cli.main",
        "tournament",
        "--tracks", tracks,
        "--races", str(races),
        "--laps", str(laps),
        "--car-dir", "cars",
        "--data-dir", data_dir,
        "--output-dir", output_dir,
    ]
    result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=False)
    return result.returncode


def check_data_files(data_dir):
    """List and summarise data files created by learning cars."""
    full_path = os.path.join(PROJECT_ROOT, data_dir)
    if not os.path.isdir(full_path):
        print(f"  [no data dir at {data_dir}]")
        return
    files = sorted(f for f in os.listdir(full_path) if f.endswith(".json"))
    if not files:
        print("  [no data files yet]")
        return
    import json
    for fname in files:
        fpath = os.path.join(full_path, fname)
        with open(fpath) as f:
            data = json.load(f)
        size = os.path.getsize(fpath)
        keys = list(data.keys())[:4]
        print(f"  {fname}: {size} bytes, keys={keys}")


def main():
    print("=" * 60)
    print("NPC Race — Adaptive Intelligence Demo")
    print("Sprint 4: Cross-race learning cars")
    print("=" * 60)

    # Clean up previous demo data
    demo_data = "cars/data_demo"
    demo_out = "demo_output"
    import shutil
    for d in (demo_data, demo_out):
        full = os.path.join(PROJECT_ROOT, d)
        if os.path.isdir(full):
            shutil.rmtree(full)

    print("\n--- Monaco: 3 races (cars learn pit strategy) ---")
    rc = run_tournament("monaco", races=3, laps=3, data_dir=demo_data, output_dir=demo_out)
    if rc != 0:
        print(f"Tournament exited with code {rc}")
        return rc

    print("\nData files after Monaco tournament:")
    check_data_files(demo_data)

    print("\n--- Monza: 5 races (cars apply + refine learning) ---")
    rc = run_tournament("monza", races=5, laps=2, data_dir=demo_data, output_dir=demo_out)
    if rc != 0:
        print(f"Tournament exited with code {rc}")
        return rc

    print("\nData files after Monza tournament:")
    check_data_files(demo_data)

    print("\n" + "=" * 60)
    print("Demo complete. Cars have now learned across 8 races.")
    print("Run again to see strategy decisions based on learned data.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
