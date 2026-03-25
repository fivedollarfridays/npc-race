# Current State

> Last updated: 2026-03-24. Sprint 40 in progress.

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
- Sprint 40 complete. Next: Sprint 41 Wave 1 (T41.1 race orchestrator).

## Sprint 40 — Progress

### What Was Just Done

- **T40.6 done**: Car analysis endpoint (server/routes/analysis.py) + editor sidebar panels. POST /api/car-analysis detects 10 known parts via AST, determines league tier (F3/F2/Championship), computes code quality (cyclomatic complexity + reliability score). Editor.html updated with parts grid, league badge, quality meter bar, and debounced auto-analyze on typing (300ms). 16 new tests (9 endpoint + 5 editor + 2 existing updated), 85 total server tests green.
- **T40.5 done**: Car editor page (server/static/editor.html) with Monaco editor from CDN, car template pre-populated, submit flow (POST /api/submit-car + auto-join lobby), lobby status polling every 2s, dark theme matching landing page. 273 lines, 11 new tests passing.
- **T40.3 done**: Fill cars module (server/fill_cars.py). Loads rival cars from cars/ directory, shuffles with optional seed, excludes player car names, returns lobby-compatible dicts with car_id=None, player_id="ai". 6 new tests passing.
- **T40.2 done**: Lobby API routes (server/routes/lobby.py). POST /api/lobby/join validates car ownership, maps Lobby errors to HTTP 404/403/409. GET /api/lobby/status returns public lobby state. Global lobby with reset_lobby() for testing. Wired into app.py. 5 new tests passing, 60 total server tests green.
- **T40.1 done**: Lobby class (server/lobby.py) with join/status/check_trigger/fill. Thread-safe with lock. Validates full lobby, duplicate players, closed lobby. Triggers on timeout or full grid, generates race_id. 9 new tests passing, 49 total server tests green.
- **T40.4 done**: Landing page (server/static/index.html) — F1-themed dark page with CODE CIRCUIT header, tagline, BUILD YOUR CAR button linking to editor, How It Works section, Tracks section. Pure HTML/CSS with JetBrains Mono, purple/green accents, responsive layout. Editor stub (editor.html) created. 7 new tests passing, 45 total server tests green.

## Sprint 40 — Lobby + Landing + Editor (24 Cx)

```
Wave 1: T40.1 (lobby) ✅, T40.4 (landing page) ✅           [8 Cx]
Wave 2: T40.2 (lobby routes) ✅, T40.3 (fill cars) ✅        [6 Cx]
Wave 3: T40.5 (editor with Monaco) ✅                        [5 Cx]
Wave 4: T40.6 (analysis panels) ✅                          [5 Cx]
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
