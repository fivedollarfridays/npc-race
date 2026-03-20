# NPC Race — Get Sellable (Public Release)

**Plan type:** feature
**Status:** Sprint 1, one blocking task remaining (T1.5 — engine integration). 186 tests passing. 20 track presets, 5 seed cars balanced. CLI works for init/validate/list-tracks/wizard.
**Estimated complexity:** 55 points
**Sprint budget:** 1 sprint (1 day)

## Tasks

### T1: Complete engine integration — T1.5 (15 pts)
- Wire `tracks.py` into `engine/simulation.py` for track-by-name selection
- Update `run_race()` signature to accept `track_name` parameter
- Integration point: `race_runner.py` loads track by name or generates procedural
- **Acceptance:** `run_race(..., track_name="monza")` uses Monza track data. All existing tests still pass.

### T2: Add --track CLI flag — T1.6 (10 pts)
- Add `--track <name>` flag to `npcrace run` command
- Add `--list-tracks` subcommand output shows all 20 presets
- **Depends on:** T1
- **Acceptance:** `npcrace run --track monza` works, `npcrace list-tracks` shows all 20

### T3: Viewer track header — T1.8 (5 pts)
- Display track name in viewer output/replay header
- **Depends on:** T1
- **Acceptance:** Viewer shows track name when loading replay

### T4: Full test suite + arch check (5 pts)
- Run full pytest suite, confirm all pass (should be 200+ after T1-T3)
- Run `bpsai-pair arch check` on all source files
- **Depends on:** T1, T2, T3
- **Acceptance:** All tests green, arch check passes

### T5: PyPI publish (15 pts)
- Bump version to 1.0.0 in pyproject.toml
- Build: `python -m build`
- Test on TestPyPI, then publish to PyPI
- Verify: `pip install npc-race && npcrace init && npcrace run` in clean venv
- **Depends on:** T4
- **Acceptance:** Package installs and runs from PyPI

### T6: GitHub release (5 pts)
- Tag v1.0.0, create GitHub release with notes
- **Depends on:** T5
- **Acceptance:** Release page shows v1.0.0

## What to skip
- Don't build additional tracks beyond 20 presets
- Don't add multiplayer/server mode
- Don't polish viewer beyond track header (T3)

## Note
NPC Race can start immediately — it does NOT depend on NPC Wars being published first. The shared architecture patterns from Wars are already proven.
