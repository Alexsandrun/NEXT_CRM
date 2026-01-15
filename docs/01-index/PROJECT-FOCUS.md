# PROJECT-FOCUS.md
Project: Next_CRM / Nexus Business OS

## 1) Target Customer
- Medium / large companies with:
  - multiple stores, warehouses, remote branches
  - analytics + finance + ops departments
  - need for data isolation between org units (tenants / subdivisions)
  - mixed connectivity (good HQ internet, слабые каналы на удалённых точках)

## 2) Product Strategy
- Start with a **ready-to-sell “Sales CRM” base model** (Bitrix24-like, but leaner):
  - agents / deals / customers / products / warehouses / price lists
  - minimal customization at first (lower onboarding cost)
- Expand via modules (LEGO approach):
  - connectors (1C, banks, marketplaces)
  - Scout (data collection/parsing)
  - Oracle (analytics/forecasting)
  - BPM (tasks, approvals, reminders)

## 3) Deployment Philosophy
- Cloud-first design (war-time resilience, modern trend), but:
  - must run locally (dev laptop) via Docker Compose
  - must support hybrid (on-prem + cloud) when needed
- Separate concerns:
  - API plane (gateway/core)
  - data plane (postgres/redis)
  - content plane (content service + quarantine pipeline)

## 4) Architecture Invariants (high-level)
- Multi-tenant isolation: `tenant_id` everywhere.
- Server-side access control (field-level stripping via Access Profiles).
- Query DSL only: clients never send SQL.
- CRM Guard: behavioral budgets + incidents + lock + revoke sessions.
- Quarantine-first for files/attachments; short-lived download tokens.
- JSON logs + sanitizer; security sink for sensitive events.
- Ops: root SSH disabled; opsadmin + sudo; break-glass only via emergency console.

## 5) Engineering Constraints
- Dev env: Windows 11 + WSL2 Ubuntu + VS Code (Remote WSL) + Docker Compose
- Core stack:
  - Python (FastAPI)
  - Postgres (JSONB hybrid)
  - Redis Streams (event bus)
  - Docker for all services
- Networking:
  - Gateway as front door (HTTP in dev; TLS in prod)
  - Future: optional site-to-site VPN / tunnels

## 6) What “Done” means for MVP
- A working Sales CRM:
  - tenants, users, roles, access profiles
  - customers/products/deals
  - import/export price lists
  - audit logs + CRM Guard baseline
- Connector-ready:
  - 1C via connector (file/API) with mapping
- Operational:
  - deployable to cloud
  - backup strategy documented
  - basic monitoring/alerts hooks defined

# END_FILE
