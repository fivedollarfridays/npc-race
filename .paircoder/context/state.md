# Current State

> Last updated: 2026-03-28. T47.3 done.

## Active Plan

**Plan:** Security Hardening + Quality Polish (Sprints 43-44)
**Score:** 74/100 production readiness (from 72)

## Open PRs
- #25 Sprint 46 (Ghost System) — pending CI

## Sprint 43 — Security Hardening (16 Cx)

```
Wave 1: T43.1 (auth fix) DONE, T43.2 (process sandbox) DONE, T43.3 (rate limit+size) DONE, T43.4 (exit codes) DONE  [12 Cx]
Wave 2: T43.5 (register endpoint) DONE                                                              [2 Cx]
Wave 3: T43.6 (security gate)                                                                      [2 Cx]
```

## Sprint 44 — Quality Polish (16 Cx)

```
Wave 1: T44.1 (decompose big fns) DONE, T44.2 (remaining arch+CORS+validation) DONE, T44.3 (test files) DONE [11 Cx]
Wave 2: T44.4 (type hints+Pydantic), T44.5 (UUID+pip-audit) DONE                                [5 Cx]
```

## QC Summary (v2)
- Tests: 2090/2090 pass (100%), 2.62:1 ratio
- Security: 1 critical, 4 high, 4 medium, 3 low
- Features: 65+ working, 13 CLI commands, 9 API endpoints
- Arch: 0 functions over 50-line limit (all 4 decomposed)
- Type coverage: 63.6%

## What Was Just Done

- **T47.3 done** — Progression tracking system. Expanded cli/progression.py (106 lines) with _load_progress, _save_progress, record_ghost_completion, record_race_win, get_progress_summary, reset_progress, and cmd_progress. Ghost L5 on any track unlocks midfield tier; midfield race win upgrades to front; front win upgrades to full. Wired record_ghost_completion into cli/ghost_command.py (extracted _record_win helper to stay under 50-line function limit). Added `npcrace progress` subcommand to cli/main.py. 14 tests in tests/test_progression.py covering defaults, ghost recording, tier unlocks, race wins, summary formatting, reset, and CLI command. All pass, ruff clean, arch clean (no errors).

- **T47.2 done** — Tiered `npcrace run` (default to player tier). Added `--tier` (choices: rookie/midfield/front/full) and `--full-grid` flags to the run subparser in cli/main.py. Extracted `get_player_tier()` to cli/progression.py (reads `~/.npcrace/progress.json`, defaults to "rookie"). Wired tier logic in cmd_run: `--full-grid` sets tier="full", `--tier` takes explicit value, otherwise reads from progression. Added `tier` parameter to `run_race()` and `_load_and_filter_cars()` in engine/race_runner.py; when tier is set and not "full", delegates to `load_tier_cars()` from engine/tiers.py. 14 tests in tests/test_tiered_run.py covering parser flags, progression helper, cmd_run wiring, and load_and_filter_cars tier routing. All pass, ruff clean, arch clean (no errors).

- **T47.1 done** — Tier system in car loader. Created engine/tiers.py (67 lines) with TIERS dict classifying all 19 rivals into rookie (4), midfield (6), front (5), veterans (4). TIER_GROUPS maps progression levels to cumulative tier sets. load_tier_cars() filters by tier, get_tier_for_car() returns tier name. 8 tests in tests/test_tiers.py using mocked load_all_cars. All pass, ruff clean, arch clean.

- **T44.5 done** — UUID car IDs + pip-audit in CI. Changed cars table PK from INTEGER AUTOINCREMENT to TEXT UUID. store_car() now generates uuid4 and returns str. Updated type hints in db.py (get_car), cars.py (get_car_detail), submit.py (CarResponse), lobby.py (JoinRequest). 3 new tests in test_uuid_car_ids.py. Fixed 4 existing tests across test_server_submit.py, test_server_lobby_routes.py, test_server_db.py, test_server_register.py that asserted int car_ids. Added pip-audit step to CI lint job (advisory, || true). 103 server tests pass, ruff clean, arch clean.

- **T44.2 done** — Four hardening fixes: (1) Decomposed PartsRaceSim.__init__ (80->44 lines) and step (126->26 lines) by extracting _get_hardware, _build_car_state, _build_driver, _compute_reliability, _compute_physics, _advance_car, _record_tick helpers. All 17 functions in parts_simulation.py now under 50 lines. (2) CORS tightened: allow_methods=["GET","POST"], allow_headers=["X-API-Key","Content-Type"], cors_origins now reads CORS_ORIGINS env var. (3) CAR_NAME validation: max 64 chars + alphanumeric/underscore/dash only. (4) API keys hashed with SHA-256 in DB; plaintext returned only on creation. 14 new tests in test_t44_2_hardening.py. 114 targeted tests pass, ruff clean.

- **T44.1 done** — Decomposed run_parts_tick (207->50 lines) and run_efficiency_tick (200->50 lines). Extracted 8 helpers into parts_runner.py and 7 helpers into efficiency_engine.py. Moved 8 pure efficiency functions + 2 computation helpers to new engine/efficiency_helpers.py (161 lines). efficiency_engine.py dropped from 400 to 315 lines. All 36 functions across 3 files are at or under 50 lines. 72 targeted tests pass, 2184 broader tests pass. 9 new characterization tests in test_decompose_characterization.py. Ruff clean.

- **T44.3 done** — Added 5 dedicated test files for untested engine modules: test_league_gates.py (12 tests), test_safe_call_unit.py (7 tests), test_sim_step_unit.py (7 tests), test_race_runner_unit.py (10 tests), test_track_gen_unit.py (11 tests). Total: 47 new tests. All pass, ruff clean, arch check clean.

- **T43.5 done** — Dedicated registration endpoint + removed auto-create from auth

- **T43.2 done** (auto-updated by hook)

- **T43.2**: Added process-based sandbox for server execution in engine/safe_call.py. New `USE_PROCESS` flag routes to `_safe_call_with_process()` which uses multiprocessing.Process + Process.kill() to terminate runaway code. Thread-based path unchanged for CLI. Extracted `_make_timeout_result` and `_make_error_result` helpers (shared by both paths), which also fixed a pre-existing arch violation in `_safe_call_with_timeout` (was 54 lines, now 38). 5 new tests in test_process_sandbox.py including infinite-loop kill verification.
- **T43.4**: Fixed CLI exit codes — 6 commands now return int instead of None. Fixed: cmd_validate (0/1), cmd_list_tracks (0), cmd_tournament (0/1), cmd_season (0), cmd_qualify (0/1), cmd_race (0/1). Also fixed cmd_run type hint from `int | None` to `int`. Updated 2 existing tests in test_cli.py that regressed. Added 9 new tests in test_cli_errors.py. All 30 CLI tests pass.
- **T43.3**: Added slowapi rate limiting (10/min on submit-car, 5/min on lobby/join) and 32KB source size cap via Pydantic max_length + explicit check. Extracted limiter to server/rate_limit.py to avoid circular imports. 6 new tests in test_server_rate_limit.py. Added slowapi to pyproject.toml server deps.
- **T43.1**: Fixed GET /api/cars/{car_id} — added auth dependency + ownership check. Invalid API key returns 401, non-owner returns 404 (prevents enumeration). List endpoint already excluded source. Updated test_server_endpoints.py to pass auth header. 4 new tests in test_server_car_security.py.

## What's Next

- T47.4+ (remaining tier sprint tasks), T44.4 (type hints+Pydantic), T43.6 (security gate)
