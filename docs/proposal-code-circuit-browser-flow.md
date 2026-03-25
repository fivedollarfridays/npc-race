# Code Circuit — Browser Player Flow Remediation

> Proposal to add a complete browser-based player experience to Code Circuit (formerly NPC Race).

## Current State

Code Circuit has a **world-class viewer** — 3-layer canvas, WebSocket 30fps streaming, spatial audio, 4 camera modes, full telemetry HUD. But everything before "watch the race" is CLI-only. There's no web server, no bot upload, no lobby, no way to go from browser to race without a terminal.

**What works today:** `python play.py --live` → browser opens → WebSocket streams race → results overlay

**What should work:** Landing → upload car → lobby (see grid) → lights out → live race → results → race again

## Principles

- **Viewer is the anchor.** The dashboard is the best thing in this project. Everything else feeds into it.
- **Minimal server.** FastAPI like Kill Switch, but thinner — no cosmetics, no tournaments yet.
- **Copy patterns from Kill Switch.** Lobby, submit, match queue — same architecture, race-specific data.
- **No premature extraction.** Copy, adapt, ship. Extract `npc-sandbox` after both games work.
- **WebSocket-native.** Code Circuit already streams via WebSocket. Keep that as the primary mode (not replay-first like Kill Switch).

---

## Phase 0: Server Bootstrap

Code Circuit has no server. Build the minimum viable server layer.

### 0.1 FastAPI App Skeleton

Create `server/` directory mirroring Kill Switch structure:

```
server/
├── app.py              # FastAPI app, CORS, static mount
├── config.py           # Port, data dir, settings
├── db.py               # SQLite init (cars table, players table)
├── auth.py             # Auto-generated API key (copy from Kill Switch)
├── routes/
│   ├── __init__.py
│   ├── health.py       # GET /api/health
│   ├── submit.py       # POST /api/submit-car
│   ├── cars.py         # GET /api/cars
│   ├── lobby.py        # POST /api/lobby/join, GET /api/lobby/status
│   ├── match.py        # GET /api/race/{id}
│   └── pages.py        # HTML page routes
└── static/
    ├── index.html       # Landing page
    ├── editor.html      # Car code editor
    └── leaderboard.html # Rankings
```

**Copy from Kill Switch:** `auth.py`, `db.py` (adapt schema), route patterns.

**Add to `pyproject.toml`:**
```toml
[project.optional-dependencies]
server = ["fastapi>=0.115", "uvicorn>=0.34"]
```

### 0.2 Car Submission Endpoint

`POST /api/submit-car` — accepts car Python source code.

**Flow:**
1. Receive source code string
2. Run through `security/bot_scanner.py` (port from Kill Switch, flip to allowlist)
3. Validate via `engine/car_loader.py` — check parts exist, league compliance
4. Store in SQLite: `cars` table (id, player_id, name, source, league_tier, created_at)
5. Return `{car_id, name, league, parts_detected: [...]}`

**Key difference from Kill Switch:** Car validation is more complex (10-part system, league gates, code quality scoring). Surface all of this in the response so the editor can show it.

### 0.3 Security Scanner (Port from Kill Switch)

Copy `security/bot_scanner.py` from Kill Switch → Code Circuit.

**Critical change:** Flip from blocklist to allowlist model per the build spec:
- Allowed imports: `{math, random, collections, itertools, functools}`
- Block everything else at AST level
- Add Code Circuit-specific allowed modules if needed (none expected)

### 0.4 Lobby + Match Queue

Copy lobby pattern from Kill Switch, adapt for racing:

- `server/lobby.py` — collect cars, timer (60s for races — longer than Kill Switch's 30s)
- Fill with AI cars if < 8 humans (use existing example cars from `cars/`)
- When lobby closes: build car configs, run race via `engine/race_runner.py`
- Store replay JSON, return `race_id`

**Key difference:** Kill Switch matches are fast (~5s). Races take 30-60s. The lobby→race→results cycle is slower, so SSE progress updates matter more.

---

## Phase 1: Wire the Browser Flow

### 1.1 Landing Page (`/`)

`server/static/index.html`:

- Game title: "Code Circuit" + tagline
- **Quick Race** → editor (write car, auto-queue)
- **Track selector** — dropdown of available tracks (fetch from `GET /api/tracks`)
- **League indicator** — F3/F2/F1 based on car complexity
- Leaderboard link
- Past races link

**New endpoint:** `GET /api/tracks` — returns list of track names from `tracks/` directory.

### 1.2 Car Editor Page

`server/static/editor.html`:

Monaco editor (same as Kill Switch) with racing-specific additions:

- **Part detection panel** — as user types, show which of 10 parts are detected:
  ```
  ✓ gearbox    ✓ cooling    ✓ strategy
  ○ aero       ○ fuel       ○ tires
  ○ suspension ○ powertrain ○ brakes ○ comms
  ```
- **League tier indicator** — "Your car qualifies for: F3" (updates live)
- **Code quality score** — complexity meter (simpler = more reliable)
- **Submit** → POST `/api/submit-car` → join lobby
- **Validation errors** shown inline (missing `decide()`, banned imports, etc.)

### 1.3 Lobby → Grid View

After submit, editor transitions to lobby state (or redirects to `lobby.html`):

- Poll `GET /api/lobby/status` every 2s
- Show **starting grid**: car names in grid position order
- Show track name + lap count
- Countdown timer (60s or until grid full)
- Fill car indicators (which slots are AI)
- When race starts: redirect to dashboard viewer

### 1.4 Dashboard Integration

The existing `viewer/dashboard.html` is the gameplay screen. Wire it to the server:

**Current flow:** WebSocket to `ws://localhost:8766` (hardcoded)

**New flow:**
1. Server starts race, opens WebSocket on dynamic port
2. Lobby status returns `{ws_url: "ws://host:port", race_id: "..."}`
3. Dashboard connects to provided `ws_url`
4. Race streams at 30fps as normal
5. When race finishes, server sends `results` message
6. Dashboard shows results overlay (already implemented)

**Changes to `viewer/js/main.js`:**
- Accept `ws_url` from URL param: `dashboard.html?ws=ws://host:port`
- Fall back to `ws://localhost:8766` if no param (backwards compat for CLI mode)

### 1.5 Results → Race Again

When race finishes:

- Dashboard already shows results overlay
- **Add buttons:** "Race Again" (→ editor with car preserved), "Leaderboard" (→ rankings)
- Store car source in `localStorage` for quick re-entry
- **New endpoint:** `GET /api/race/{id}/results` — lightweight results JSON (positions, times, events)

---

## Phase 2: Polish

### 2.1 Lights Out Countdown

Between lobby close and race start, add the F1-style lights sequence:

- Dashboard receives `{type: "countdown", seconds: 5}` before `init` message
- Canvas renders: 5 red lights appear one by one (1 per second)
- All lights go out → race starts
- Audio: ascending tone per light, horn on lights out
- Total: 5 seconds of anticipation

**Scope:** ~80 lines JS in dashboard + 1 new WebSocket message type from server.

### 2.2 Race Progress SSE (For Spectators)

Not everyone watches via WebSocket. Add an SSE endpoint for lighter-weight updates:

- `GET /api/race/{id}/stream` — SSE events every 2s with positions, lap counts, gaps
- Useful for: lobby page showing "race in progress", leaderboard live updates, Discord bot
- Dashboard still uses full WebSocket for 30fps rendering

### 2.3 Qualifying Mode

Before the race, run a qualifying session to determine grid order:

- Each car gets 1 hot lap alone on track
- Lap time determines starting position
- Show qualifying results before race countdown
- Adds ~15s to the flow but makes grid order meaningful

### 2.4 Replay Storage + History

- Store replay JSON in `data/replays/` (or SQLite blob)
- `GET /api/races` — list recent races with track, winner, date
- `GET /api/race/{id}/replay` — download replay JSON
- Dashboard can load replays: `dashboard.html?replay=/api/race/{id}/replay`
- Race history page showing past results

---

## Phase 3: Stretch Goals

### 3.1 Championship Mode

Multi-race series with points accumulation:
- Define championship: 5 tracks, 3 laps each
- Points per position (25-18-15-12-10-8-6-4-2-1)
- Championship standings page
- Final race decides champion

### 3.2 Pit Strategy Visualization

The dashboard already shows pit stops in telemetry. Enhance:
- Pit window indicator on timeline
- Tire degradation curve overlay
- Strategy comparison between cars post-race

### 3.3 Car Workshop Page

Dedicated page for car development (beyond the editor):
- Visual car schematic showing all 10 parts
- Per-part code editor tabs
- Telemetry from test laps
- League progression tracker

---

## Sprint Mapping (Estimated)

| Sprint | Focus | Cx | Outcome |
|--------|-------|----|---------|
| CC-S1 | 0.1-0.3 Server bootstrap + security scanner | 85 | FastAPI app running, submit endpoint works |
| CC-S2 | 0.4 Lobby + 1.1 Landing + 1.2 Editor | 90 | Can submit car from browser, lobby collects |
| CC-S3 | 1.3 Grid view + 1.4 Dashboard wiring + 1.5 Results | 85 | Complete flow: editor → lobby → race → results |
| CC-S4 | 2.1 Lights out + 2.2 SSE + 2.3 Qualifying | 80 | Polished pre-race experience |
| CC-S5 | 2.4 Replay storage + 3.x stretch | TBD | History, championships |

## What We're NOT Doing

- **No Redis.** Races are slower and less frequent than Kill Switch matches. In-memory queue is fine to start.
- **No tournaments yet.** Championship mode is Phase 3. Single races first.
- **No mobile.** Dashboard is a complex canvas app — desktop only.
- **No shared SDK extraction.** Copy from Kill Switch, adapt. Extract `npc-sandbox` after both work.
- **No Docker sandbox yet.** AST scanner + subprocess isolation first. Docker is Tier 3 for ranked mode.
- **No Discord integration yet.** Browser flow first, Discord ranked mode comes later per build spec.
