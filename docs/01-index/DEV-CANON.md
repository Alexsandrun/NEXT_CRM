# Dev Canon (Next_CRM)

## Rules
- Docs-first: design/spec in docs before implementation.
- Canon > Code: if mismatch, update code OR write ADR to justify change.
- One block at a time: implement only current block scope.
- Every block must ship:
  - docs (scope + DoD)
  - runnable compose/dev setup (if applicable)
  - smoke test
  - minimal demo steps

## Branching
- Work in `block-N-*` branches
- Merge via PR to `main`
- PR includes DoD checklist from the block doc

## ADR
- Any architecture change => append entry in `docs/01-index/ADR-LOG.md`

# END_FILE
