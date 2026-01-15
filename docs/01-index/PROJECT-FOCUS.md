# PROJECT FOCUS: Next_CRM / Nexus Business OS

## MEMORY RULESET (Dev Canon)
- Canonical docs entrypoint: `docs/01-index/ARCHITECTURE-INDEX.machine.md` (always consult before coding).
- Canon > Code: if conflict, docs win; architecture changes require updating docs + adding ADR in `docs/01-index/ADR-LOG.md`.
- Follow implementation order: `docs/01-index/NEXT-STEPS-ROADMAP.md` (Sprint 0..8).
- Non-negotiable invariants:
  1) `tenant_id` isolation everywhere; no cross-tenant without explicit export/import.
  2) Server-side field stripping via Access Profiles (UI is never the only control).
  3) Query DSL only; clients never send SQL (allowlists + caps enforced).
  4) CRM Guard budgets warn/block + incidents + user lock + revoke sessions.
  5) Quarantine-first content pipeline + short-lived download tokens.
  6) JSON logging + sanitizer + SECURITY sink.
  7) Root SSH disabled; opsadmin + sudo; break-glass via emergency console only.
- Any new module/spec must be added to `ARCHITECTURE-INDEX.machine.md` with keywords.

# END_FILE
