# Current State

> Last updated: 2026-03-26. QC audit v2 complete. Ready for S43-44.

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
Wave 1: T44.1 (decompose big fns), T44.2 (remaining arch+CORS+validation), T44.3 (test files) [11 Cx]
Wave 2: T44.4 (type hints+Pydantic), T44.5 (UUID+pip-audit)                                     [5 Cx]
```

## QC Summary (v2)
- Tests: 2090/2090 pass (100%), 2.62:1 ratio
- Security: 1 critical, 4 high, 4 medium, 3 low
- Features: 65+ working, 13 CLI commands, 9 API endpoints
- Arch: 4 functions over 50-line limit
- Type coverage: 63.6%

## What Was Just Done

- **T43.5 done** — Dedicated registration endpoint + removed auto-create from auth

- **T43.2 done** (auto-updated by hook)

- **T43.2**: Added process-based sandbox for server execution in engine/safe_call.py. New `USE_PROCESS` flag routes to `_safe_call_with_process()` which uses multiprocessing.Process + Process.kill() to terminate runaway code. Thread-based path unchanged for CLI. Extracted `_make_timeout_result` and `_make_error_result` helpers (shared by both paths), which also fixed a pre-existing arch violation in `_safe_call_with_timeout` (was 54 lines, now 38). 5 new tests in test_process_sandbox.py including infinite-loop kill verification.
- **T43.4**: Fixed CLI exit codes — 6 commands now return int instead of None. Fixed: cmd_validate (0/1), cmd_list_tracks (0), cmd_tournament (0/1), cmd_season (0), cmd_qualify (0/1), cmd_race (0/1). Also fixed cmd_run type hint from `int | None` to `int`. Updated 2 existing tests in test_cli.py that regressed. Added 9 new tests in test_cli_errors.py. All 30 CLI tests pass.
- **T43.3**: Added slowapi rate limiting (10/min on submit-car, 5/min on lobby/join) and 32KB source size cap via Pydantic max_length + explicit check. Extracted limiter to server/rate_limit.py to avoid circular imports. 6 new tests in test_server_rate_limit.py. Added slowapi to pyproject.toml server deps.
- **T43.1**: Fixed GET /api/cars/{car_id} — added auth dependency + ownership check. Invalid API key returns 401, non-owner returns 404 (prevents enumeration). List endpoint already excluded source. Updated test_server_endpoints.py to pass auth header. 4 new tests in test_server_car_security.py.

## What's Next

- T43.6 (security gate)
