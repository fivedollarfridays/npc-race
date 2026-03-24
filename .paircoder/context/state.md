# Current State

> Last updated: 2026-03-24. Sprint 39 in progress.

## Active Plan

**Plan:** Code Circuit Browser Flow (Sprints 39-41)
**Reference:** docs/proposal-code-circuit-browser-flow.md

## Completed

| Phase | Sprints | Status |
|-------|---------|--------|
| Core physics + quality | S23-28 | ✅ |
| Car projects + league | S29-31 | ✅ |
| Submission + leaderboard | S32-33 | ✅ |
| Fast sim + qualifying | S34 | ✅ |
| Full grid + real distances | S35 | ✅ |
| Test tiers | S36 | ✅ |
| Onboarding bugfixes | S37 | ✅ |
| Audit bugfixes | S38 | ✅ |

## Sprint 39 — Server Bootstrap (18 Cx)

```
Wave 1: T39.1 (FastAPI app) ✅, T39.2 (SQLite DB) ✅      [6 Cx]
Wave 2: T39.3 (auth) ✅, T39.4 (health) ✅                 [4 Cx]
Wave 3: T39.5 (submit-car) ✅, T39.6 (cars+tracks) ✅      [8 Cx]
```

### What Was Just Done

- **T39.6 done** (auto-updated by hook)

- **T39.6 done**: GET /api/cars + GET /api/tracks endpoints. Cars route lists player's cars (auth required) and gets car detail by ID (404 if not found). Tracks route returns all 20 tracks with metadata. 6 new tests passing, 33 total server tests green.
- **T39.5 done**: POST /api/submit-car endpoint (server/routes/submit.py). Validates empty source, runs bot_scanner security scan, extracts CAR_NAME/CAR_COLOR from AST, stores car in DB. Auto-creates player on first submit (returns api_key). 6 tests passing, 27 total server tests green.
- **T39.3 done** (auto-updated by hook)
- **T39.3 done**: API key auth dependency (server/auth.py). Auto-creates player + key on first request, validates existing keys, returns 401 on invalid. 3 tests passing, 21 total server tests green.
- **T39.4 done**: GET /api/health endpoint returning {"status": "ok", "version": "0.1.0"}. Created server/routes/ package with health router wired into app. 3 tests passing, 21 total server tests green.
- T39.1: FastAPI app skeleton with config, CORS middleware, and static/viewer mounts. 6 tests passing.
- T39.2: SQLite DB layer with players, api_keys, cars tables. All CRUD ops (create/get player, API keys, store/get cars). 9 tests passing.

### What's Next
- Sprint 39 complete. Ready for Sprint 40 (Lobby + Landing + Editor).

## Sprint 40 — Lobby + Landing + Editor (24 Cx)

```
Wave 1: T40.1 (lobby), T40.4 (landing page)               [8 Cx]
Wave 2: T40.2 (lobby routes), T40.3 (fill cars)            [6 Cx]
Wave 3: T40.5 (editor with Monaco)                         [5 Cx]
Wave 4: T40.6 (analysis panels)                            [5 Cx]
```

## Sprint 41 — Grid + Dashboard + Results (19 Cx)

```
Wave 1: T41.1 (race orchestrator)                          [5 Cx]
Wave 2: T41.2 (race API), T41.3 (grid), T41.4 (dashboard)  [9 Cx]
Wave 3: T41.5 (results overlay), T41.6 (localStorage)      [5 Cx]
```

## Key Metrics

- **~2,400 tests** | **20 cars** | **20 tracks** | CI green
- Game playable end-to-end via CLI
- Browser flow: landing → editor → lobby → race → results (3 sprints)
