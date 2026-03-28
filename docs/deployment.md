# Deployment Guide

## Quick Start

```bash
# Local
uvicorn server.app:app --host 0.0.0.0 --port 8000

# Docker
docker build -t npc-race .
docker run -p 8000:8000 npc-race
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated allowed origins | localhost + agentgrounds.ai |
| `PORT` | Server port (used by Procfile) | 8000 |

## Health Check

```
GET /api/health
```

Returns `{"status": "ok", "version": "0.1.0"}`.

## Platform Deployment

### Railway / Heroku

The `Procfile` handles process configuration automatically.
The `PORT` environment variable is set by the platform.

### Docker

The `Dockerfile` uses `python:3.13-slim`, installs the `[server]` extras,
and runs uvicorn on port 8000.

## CORS Configuration

Set `CORS_ORIGINS` to a comma-separated list of allowed origins:

```bash
CORS_ORIGINS="https://myapp.com,https://staging.myapp.com"
```

Default origins include localhost ports and agentgrounds.ai.
