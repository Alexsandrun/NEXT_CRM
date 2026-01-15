# ARCHITECTURE-INDEX.machine.md
Project: Next_CRM / Nexus Business OS
Purpose: Machine-oriented index of canonical docs (keywords-first). Use this as entrypoint before coding.

## Project Focus
- Focus: Next_CRM (Nexus Business OS)
- Canon sources (order):
  1) docs/01-index/ARCHITECTURE-INDEX.machine.md (this file)
  2) docs/01-index/PROJECT-FOCUS.md
  3) docs/01-index/DEV-CANON.md
  4) docs/01-index/NEXT-STEPS-ROADMAP.md
  5) docs/01-index/ADR-LOG.md
- Rule: If docs conflict with code, docs win. Architecture changes require ADR.

## Keywords (Core Concepts)
- multi_tenant, tenant_id, isolation, scoping
- rbac, roles, permissions, access_profiles, field_level_security
- query_dsl, allowlist, caps, pagination, rate_limit
- crm_guard, budgets, anomaly_detection, incidents, lock_user, revoke_sessions
- nxp_envelope, trace_id, signature, routing, route_id
- event_bus, redis_streams, consumers, retry, idempotency
- content_pipeline, quarantine, sanitizer, attachments, short_lived_tokens
- audit_logs, security_logs, immutable_logs, tamper_evidence
- ops, break_glass, emergency_console, bastion, no_root_ssh

## Canonical Documents Map
### 01-index (Entry & Governance)
- docs/01-index/PROJECT-FOCUS.md
  - keywords: project_scope, target_customer, deployment, cloud_first, dev_env
- docs/01-index/DEV-CANON.md
  - keywords: invariants, non_negotiables, coding_rules, doc_first
- docs/01-index/NEXT-STEPS-ROADMAP.md
  - keywords: phases, sprints, implementation_order, block_plan
- docs/01-index/ADR-LOG.md
  - keywords: decisions, tradeoffs, history, change_control

### 03-protocols (Contracts)
- docs/03-protocols/NXP-ENVELOPE.md
  - keywords: envelope, header, security, routing, payload, trace_id, versioning
- docs/03-protocols/ERROR-CONTRACT.md
  - keywords: error_code, message, details, retryable, trace_id, http_mapping
- docs/03-protocols/QUERY-DSL.md
  - keywords: query_language, allowlist, filters, sorting, pagination, caps

### 02-architecture (System)
- docs/02-architecture/CORE-MANAGER.md
  - keywords: registrar, dispatcher, lifecycle, licensing, topology
- docs/02-architecture/MULTI-TENANCY.md
  - keywords: tenant_model, org_units, isolation_boundaries, export_import
- docs/02-architecture/SECURITY-MODEL.md
  - keywords: zero_trust, pki, jwt, signing, key_rotation, audit

### 04-modules (Domain)
- docs/04-modules/CRM-GUARD.md
  - keywords: budgets, thresholds, warnings, blocks, incident_workflow
- docs/04-modules/CRM-BASE.md
  - keywords: entities, cards, jsonb, workflows, sales_model
- docs/04-modules/CONNECTORS.md
  - keywords: 1c_connector, import_export, pricing, analytics_packs

### 05-devops (Runbooks)
- docs/05-devops/DEV-ENV.md
  - keywords: wsl, docker_compose, ports, troubleshooting, smoke
- docs/05-devops/OPS-ACCESS.md
  - keywords: ssh_policy, opsadmin, sudo, break_glass, alerts

## Current Repo Reality (Block 0)
- docker-compose.yml: gateway/core/content/runner/postgres/redis
- infra/nginx/dev.conf: routes /health, /api/*, /content/*
- scripts/smoke.sh: waits and checks health endpoints
- services:
  - services/core/app/main.py: /health
  - services/content/app/main.py: /health
  - services/runner/app/runner.py: redis ping loop

## Next Files To Create (Block 1)
1) docs/01-index/PROJECT-FOCUS.md
2) docs/01-index/DEV-CANON.md
3) docs/01-index/NEXT-STEPS-ROADMAP.md
4) docs/01-index/ADR-LOG.md
5) docs/03-protocols/NXP-ENVELOPE.md
6) docs/03-protocols/ERROR-CONTRACT.md
7) docs/03-protocols/QUERY-DSL.md

# END_FILE
