# Current State

> Last updated: 2026-03-28. Sprint 47 merged. Planning S48 integration.

## Active Plan

**Plan:** Agentgrounds.ai Integration (Sprint 48)
**Goal:** Code Circuit playable from agentgrounds.ai arcade

## Completed Sprints (S33-S47)

| Sprint | What |
|--------|------|
| S33-S38 | Core game, qualifying, leaderboard, testing, audit |
| S39-S40 | Server + lobby + editor |
| S42 | PartsRaceSim (game-fixing) |
| S43 | Security hardening |
| S44 | Quality polish |
| S45 | Time trial + coaching (0.5s loop) |
| S46 | Ghost system + efficiency HUD |
| S47 | Tiered grid + progression |

## Sprint 48 — Agentgrounds.ai Integration (13 Cx)

**Cross-repo: agentgrounds-web (frontend) + npc-race (backend)**

```
Wave 1 (parallel): T48.1 (API proxy), T48.2 (logo+transition), T48.4 (CRT UI) [8 Cx]
Wave 2:            T48.3 (flip to LIVE), T48.5 (deployment config)              [3 Cx]
Wave 3 (GATE):     T48.6 (end-to-end integration)                               [2 Cx]
```

## What Was Just Done

- **T48.5**: Backend deployment config for npc-race
  - Created Dockerfile (python:3.13-slim, installs [server] extras, uvicorn CMD)
  - Created Procfile (web process with $PORT env var for Railway/Heroku)
  - Verified CORS_ORIGINS env var support already in server/config.py
  - Created docs/deployment.md (env vars, health check, platform guides)
  - 11 tests in tests/test_deployment.py, all passing
- **T48.3**: Flipped Code Circuit to LIVE in agentgrounds-web (prior session)
- **T48.4**: CRT-compatible game UI for npc-race backend (prior session)
- **T48.2**: Code Circuit logo + transition wiring in agentgrounds-web (prior session)

## What's Next

- T48.1 (API proxy) — remaining Wave 1 task
- T48.6 (end-to-end integration) — Wave 3 GATE

## QC Status
- 9 suites (5 browser + 4 game fun), all valid
- Game fun QC: 16/16 pass
- API QC: 9/9 pass
