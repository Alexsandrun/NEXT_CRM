#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8088}"

echo "== wait gateway =="
for i in {1..40}; do
  code="$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)"
  if [[ "$code" == "200" ]]; then
    echo "gateway ok"
    break
  fi
  echo "wait gateway... ($i) http=$code"
  sleep 1
done
echo

echo "== bootstrap ==" && curl -sS -X POST "$BASE/api/bootstrap" && echo
echo

echo "== login =="
login_json="$(curl -sS -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
echo "$login_json"
token="$(printf '%s' "$login_json" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
echo "token=$token"
echo

ts="$(date +%s)"

echo "== create pipeline =="
p_json="$(curl -sS -X POST "$BASE/api/pipelines" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Sales $ts\"}")"
echo "$p_json"
pipeline_id="$(printf '%s' "$p_json" | sed -n 's/.*"pipeline_id":"\([^"]*\)".*/\1/p')"
echo "pipeline_id=$pipeline_id"
echo

echo "== create stage #1 (New) =="
s1_json="$(curl -sS -X POST "$BASE/api/stages" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"New\",\"sort_order\":10,\"is_won\":false,\"is_lost\":false}")"
echo "$s1_json"
stage1_id="$(printf '%s' "$s1_json" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
echo "stage1_id=$stage1_id"
echo

echo "== create stage #2 (Won) =="
s2_json="$(curl -sS -X POST "$BASE/api/stages" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"Won\",\"sort_order\":99,\"is_won\":true,\"is_lost\":false}")"
echo "$s2_json"
stage2_id="$(printf '%s' "$s2_json" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
echo "stage2_id=$stage2_id"
echo

echo "== create deal in New =="
d_json="$(curl -sS -X POST "$BASE/api/deals" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"title\":\"Deal $ts\",\"amount\":\"1000.00\",\"currency\":\"USD\",\"company_id\":null,\"contact_id\":null,\"pipeline_id\":\"$pipeline_id\",\"stage_id\":\"$stage1_id\"}")"
echo "$d_json"
deal_id="$(printf '%s' "$d_json" | sed -n 's/.*"deal_id":"\([^"]*\)".*/\1/p')"
echo "deal_id=$deal_id"
echo

echo "== board =="
curl -sS "$BASE/api/pipelines/$pipeline_id/board" -H "Authorization: Bearer $token" ; echo
echo

echo "== move deal to Won =="
curl -sS -X PATCH "$BASE/api/deals/$deal_id" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"stage_id\":\"$stage2_id\"}" ; echo
echo

echo "== board after move =="
curl -sS "$BASE/api/pipelines/$pipeline_id/board" -H "Authorization: Bearer $token" ; echo
