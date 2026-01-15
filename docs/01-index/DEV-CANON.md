# DEV-CANON.md
Dev Canon for Next_CRM / Nexus Business OS.
This is the “non-negotiable” development ruleset.

## 0) Canon > Code
- If code conflicts with docs: **docs win**.
- Any architecture change:
  1) update relevant docs
  2) add ADR entry in docs/01-index/ADR-LOG.md

## 1) Implementation Order
- Follow: docs/01-index/NEXT-STEPS-ROADMAP.md
- Build in small blocks:
  - implement → smoke → commit → push
  - never “big-bang” refactors without ADR

## 2) Non-negotiable Invariants
1) **Tenant isolation**
   - Every row has `tenant_id`.
   - No cross-tenant reads/writes without explicit export/import flow.
2) **Server-side field stripping**
   - Access Profiles define which fields are returned.
   - UI is never a security control.
3) **Query DSL only**
   - Clients never send SQL.
   - Allowlist + caps + pagination always enforced.
4) **CRM Guard**
   - User budgets: warn/block thresholds.
   - Incidents log.
   - Lock user + revoke sessions when needed.
5) **Quarantine-first content pipeline**
   - Attachments never go directly to CRM.
   - Sanitize/convert to safe formats.
   - Downloads via short-lived tokens.
6) **Logging standard**
   - JSON logs.
   - Sanitizer removes/obfuscates PII/secrets.
   - SECURITY sink for high-risk events.
7) **Ops access**
   - root SSH disabled.
   - opsadmin + sudo with audit.
   - break-glass only via emergency console/runbook.

## 3) Coding Rules (Practical)
- Services expose:
  - GET /health (no auth)
  - GET /version (build info)
- Every request:
  - trace_id (generated if missing)
  - structured logs with trace_id
- Idempotency:
  - event consumers must be idempotent
  - store processed message ids when needed
- Errors:
  - follow ERROR-CONTRACT.md
  - include trace_id always
- Config:
  - only via env vars
  - no secrets committed (.env ignored)

## 4) Repo Hygiene
- Keep docs in sync.
- Small PR/commit steps.
- Always provide a smoke script or minimal validation for each block.
- Prefer explicit typing and clear naming over cleverness.

# END_FILE
