# Current State

> Last updated: 2026-03-23 Sprint 32 complete. One sprint remaining.

## Active Plan

**Plan:** NPC Race v3 — Build a Car Out of Code (Master Plan)
**Reference:** docs/proposal-npc-race-v3.md (fully updated)

## Completed Phases

| Phase | Description | Sprints | Status |
|-------|------------|---------|--------|
| Phase 0 | Baseline measurement | S23 | ✅ |
| Phase 1 | Core physics engine | S24-28 | ✅ Closed |
| Phase 2 | Code quality → reliability | S27 | ✅ |
| Phase 3 | Multi-file car project loader | S29 | ✅ |
| Phase 4a | League system | S30 | ✅ |
| Phase 4b | Viewer additions | S31 | ✅ |
| Phase 5a | Local submission pipeline | S32 | ✅ |

## Next: Sprint 33 — Leaderboard + Onboarding (FINAL)

Closes the local product loop. After this sprint, the game is complete for local play.

- T33.1: Leaderboard module (load/add/save/format standings) -- DONE
- T33.2: Leaderboard CLI (`npcrace leaderboard --add results.json`) -- DONE
- T33.3: Onboarding (`GETTING_STARTED.md` + `npcrace init` polish) -- DONE
- T33.4: Integration gate (init → run → submit → leaderboard) -- DONE

## Future: Phase 6 — Hosted Infrastructure

Server-side execution, web leaderboard, multiplayer seasons, player accounts.
Build when there are players, not before.

## What Was Just Done

- **T33.4**: Integration gate. Wrote 8 end-to-end tests in `tests/test_integration_gate.py` exercising the full player journey: init -> run -> submit -> leaderboard add -> leaderboard show. Tests verify project creation, race execution with results export, submission validation, leaderboard accumulation across multiple races, and GETTING_STARTED.md command references. All 8 pass. Sprint 33 complete. 12/12 success criteria met.

- **T33.2**: Leaderboard CLI. Added `leaderboard` subcommand to `cli/main.py` with `--add`, `--reset`, `--file` args. Added `cmd_leaderboard` to `cli/commands.py` handling show/add/reset flows with integrity verification. All 7 CLI tests pass, 18/18 leaderboard tests total.

- **T33.3**: Onboarding polish. Rewrote `cmd_init` to copy `cars/default_project/` (car.py, gearbox.py, cooling.py, strategy.py, README.md) via `shutil.copytree`. Returns 0 on success, 1 if dir exists. Changed `init` parser from `--dir` flag to positional arg. Verified GETTING_STARTED.md has before/after RPM values (12,800 / 12,200). All 6 onboarding tests pass. Updated old test_cli.py init tests.

- **Sprint 32**: Local submission pipeline. `engine/results.py` with results summary + SHA-256 integrity hash. `npcrace submit` CLI validates results. `run_race()` auto-exports results.json. 33 tests.

- **Sprint 31**: Viewer additions. Call log export at 1Hz. Code terminal + grade card. v3.1 proposal updated.

- **Sprint 30**: League system. F3→F2→F1→Championship. Advisory + enforced quality gates.

## Key Metrics

- **1,974 tests** | **175 Python files** | **32 sprints**
- **Monza 1-lap**: 81.13s baseline, 75.33s optimized (5.80s spread)
- **Monza 5-lap**: 17.77s compound spread
- **6/9 parts above 0.3s sensitivity**
- **12/12 success criteria met** (Sprint 33 complete)
