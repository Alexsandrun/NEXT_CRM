# NEXT-STEPS-ROADMAP.md
Implementation roadmap (Sprints/Blocks) for Next_CRM.

## Block 0 (DONE) — Dev Stack Skeleton
- docker-compose dev stack: gateway/core/content/runner/postgres/redis
- nginx routing: /health, /api/*, /content/*
- smoke script

Acceptance:
- `./scripts/smoke.sh` => OK

---

## Block 1 — Canonical Contracts (Docs + Minimal Endpoints)
Goal: freeze contracts before business logic.

Deliverables:
- docs:
  - ARCHITECTURE-INDEX.machine.md (done)
  - PROJECT-FOCUS.md (done)
  - DEV-CANON.md (done)
  - ADR-LOG.md
  - protocols:
    - NXP-ENVELOPE.md
    - ERROR-CONTRACT.md
    - QUERY-DSL.md
- code:
  - core/content expose /version
  - shared request middleware: trace_id + log fields

Acceptance:
- smoke includes /version checks
- docs exist and indexed

---

## Block 2 — Identity & Tenancy (MVP)
Goal: tenant_id everywhere + auth scaffolding.

Deliverables:
- Postgres schema:
  - tenants, users, roles, sessions
- Auth:
  - JWT session token (dev simple)
- RBAC:
  - role permissions baseline
- Tenant scoping:
  - enforced in DB queries + service layer

Acceptance:
- create tenant/user
- login returns token
- token scopes tenant_id

---

## Block 3 — Access Profiles (Field-level Security)
Goal: server-side field stripping.

Deliverables:
- access_profiles table
- per-entity field allowlist
- response shaping middleware

Acceptance:
- same entity returns different fields for different profiles

---

## Block 4 — Query DSL (Search, Sort, Pagination)
Goal: safe querying without SQL from client.

Deliverables:
- Query DSL parser/validator
- allowlist per entity
- caps: max rows, max page size, max filters
- mapping -> SQLAlchemy/SQL builder

Acceptance:
- operators can list customers with filters without raw SQL

---

## Block 5 — CRM Base (Sales Model MVP)
Goal: sellable “sales CRM” base.

Deliverables:
- entities: customers, deals, products, warehouses, price_lists
- minimal UI-ready APIs
- audit logs for create/update/delete

Acceptance:
- CRUD flows + list/search via DSL

---

## Block 6 — CRM Guard (Budgets + Incidents)
Goal: detect abnormal behavior and act.

Deliverables:
- budgets per user/profile
- warn/block thresholds
- incident records
- lock user + revoke sessions

Acceptance:
- simulate burst activity => warn then block

---

## Block 7 — Content Pipeline (Quarantine + Safe Attachments)
Goal: protect against file-borne attacks.

Deliverables:
- content service:
  - upload -> quarantine
  - sanitize/convert -> safe store
  - short-lived token downloads
- CRM references content by ids

Acceptance:
- upload file => quarantined => safe artifact => accessible via token

---

## Block 8 — Event Bus (Redis Streams) + Module Skeleton
Goal: standard event envelope and module integration baseline.

Deliverables:
- event bus wrapper
- consumer group patterns
- idempotency strategy
- sample module (connector stub)

Acceptance:
- produce/consume events with NXP envelope and trace_id

# END_FILE
