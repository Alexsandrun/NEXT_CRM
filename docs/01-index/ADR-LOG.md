# ADR-LOG.md
Architecture Decision Records (ADR) — append-only log.
Rule: any architecture change must add an ADR entry.

## Template
- ADR-XXXX: <Title>
  - Date: YYYY-MM-DD
  - Status: Proposed | Accepted | Superseded
  - Context:
  - Decision:
  - Consequences:
  - Alternatives considered:
  - Links:

---

## ADR-0001: Cloud-first + Local Docker Compose Dev
- Date: 2026-01-15
- Status: Accepted
- Context:
  - Cloud is the default direction (resilience, war-time continuity), but dev must run locally.
- Decision:
  - Design cloud-first, deployable to cloud providers.
  - Dev environment uses Docker Compose on WSL2.
- Consequences:
  - All services must be container-friendly.
  - No hard dependency on on-prem-only assumptions.

---

## ADR-0002: Gateway-first routing (HTTP in dev)
- Date: 2026-01-15
- Status: Accepted
- Context:
  - Need a single entry point and future TLS / policies.
- Decision:
  - Nginx gateway routes:
    - /health -> gateway
    - /api/* -> core
    - /content/* -> content
- Consequences:
  - Browser/dev tools always use one base URL.
  - Later can swap to Envoy/Traefik without breaking contracts.

---

## ADR-0003: Query DSL only (no client SQL)
- Date: 2026-01-15
- Status: Accepted
- Context:
  - SQL injection and uncontrolled queries are high risk.
- Decision:
  - Clients send only Query DSL.
  - Server validates via allowlists and caps.
- Consequences:
  - Slight extra development effort early.
  - Strong security + predictable performance.

---

## ADR-0004: CRM Guard implemented at CRM layer (not gateway)
- Date: 2026-01-15
- Status: Accepted
- Context:
  - Gateway-level per-card transport control may harm performance for large operators.
- Decision:
  - Enforce budgets/anomaly detection in CRM/Core service layer.
- Consequences:
  - Core becomes the policy enforcement point.
  - Gateway remains mostly routing + coarse protections.

# END_FILE
