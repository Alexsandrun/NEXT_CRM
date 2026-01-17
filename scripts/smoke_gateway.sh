#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8088}"

echo "== wait /api/health =="
code=""
for i in {1..60}; do
  code="$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)"
  if [[ "$code" == "200" ]]; then
    echo "health OK"
    break
  fi
  echo "try $i http=$code"
  sleep 1
done
[[ "$code" == "200" ]] || { echo "health not OK (http=$code)"; exit 1; }

echo "== openapi has board endpoint =="
openapi="$(curl -sS "$BASE/api/openapi.json")"
grep -q '"/pipelines/{pipeline_id}/board"' <<<"$openapi"
echo "openapi OK"

echo "== bootstrap (idempotent) =="
curl -sS -X POST "$BASE/api/bootstrap" >/dev/null || true

echo "== login =="
login_json="$(curl -sS -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
TOKEN="$(sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p' <<<"$login_json")"
[[ -n "$TOKEN" ]] || { echo "login failed: $login_json"; exit 1; }

echo "== create pipeline + stages + deal =="
pipe_json="$(curl -sS -X POST "$BASE/api/pipelines" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"CI Sales"}')"
pipeline_id="$(sed -n 's/.*"pipeline_id":"\([^"]*\)".*/\1/p' <<<"$pipe_json")"
[[ -n "$pipeline_id" ]] || { echo "pipeline create failed: $pipe_json"; exit 1; }
echo "pipeline_id=$pipeline_id"

st1_json="$(curl -sS -X POST "$BASE/api/stages" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"New\",\"sort_order\":10}")"
stage1_id="$(sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p' <<<"$st1_json")"
[[ -n "$stage1_id" ]] || { echo "stage1 create failed: $st1_json"; exit 1; }

st2_json="$(curl -sS -X POST "$BASE/api/stages" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"Won\",\"sort_order\":99,\"is_won\":true}")"
stage2_id="$(sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p' <<<"$st2_json")"
[[ -n "$stage2_id" ]] || { echo "stage2 create failed: $st2_json"; exit 1; }

deal_json="$(curl -sS -X POST "$BASE/api/deals" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d "{\"title\":\"CI Deal\",\"amount\":1000,\"currency\":\"USD\",\"pipeline_id\":\"$pipeline_id\",\"stage_id\":\"$stage1_id\"}")"
deal_id="$(sed -n 's/.*"deal_id":"\([^"]*\)".*/\1/p' <<<"$deal_json")"
[[ -n "$deal_id" ]] || { echo "deal create failed: $deal_json"; exit 1; }

echo "== board request =="
board_json="$(curl -sS "$BASE/api/pipelines/$pipeline_id/board?include_empty=true" -H "Authorization: Bearer $TOKEN")"
# безопасный “head” без pipe (не ломает CI на pipefail)
printf '%s\n' "${board_json:0:600}"
grep -q '"columns"' <<<"$board_json"
echo "board OK"

echo "ALL SMOKE CHECKS PASSED"
