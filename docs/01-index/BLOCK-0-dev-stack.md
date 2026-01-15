# Block 0 — Dev Stack (Sprint 0) v1.0

Canonical refs:
- docs/01-index/PROJECT-FOCUS.md
- docs/01-index/DEV-CANON.md
- docs/01-index/ARCHITECTURE-INDEX.machine.md

---

## Goal
Bring up a reproducible local dev environment where:
- all core services start via docker compose
- DB + event bus are ready
- healthchecks pass
- a smoke test proves end-to-end wiring

## In Scope
- Docker Compose (dev) with services: gateway, core, content, runner, postgres, redis
- Basic config via `.env`
- Health endpoints for services
- DB migrations mechanism bootstrap (can be empty initially)
- Logging baseline: JSON logs with `service`, `event`, `ts`, `level` (+ `trace_id` field placeholder)
- Minimal network layout (internal docker network)

## Out of Scope
- Auth, tenancy, RBAC
- Query DSL
- CRM Guard
- Content quarantine logic (only skeleton)
- UI

## Deliverables
- docker-compose.yml (dev)
- .env.example
- services skeletons with /health
- migrations mechanism hook
- scripts/smoke.sh

## Definition of Done
- `docker compose up -d` starts all containers
- `curl http://localhost:<GATEWAY_PORT>/api/health` -> core ok
- `curl http://localhost:<GATEWAY_PORT>/content/health` -> content ok
- logs are JSON one-line
- smoke script exits 0

# END_FILE
