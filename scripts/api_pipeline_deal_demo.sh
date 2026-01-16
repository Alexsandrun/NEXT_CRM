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

echo "== bootstrap ==" && curl -sS -X POST "$BASE/api/bootstrap" ; echo
echo

echo "== login =="
login_json="$(curl -sS -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
echo "$login_json"
token="$(printf '%s' "$login_json" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
if [[ -z "${token:-}" ]]; then
  echo "ERROR: token is empty"
  exit 2
fi
echo "token=$token"
echo

ts="$(date +%s)"

echo "== create pipeline =="
pipe_json="$(curl -sS -X POST "$BASE/api/pipelines" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Sales $ts\"}")"
echo "$pipe_json"
pipeline_id="$(printf '%s' "$pipe_json" | sed -n 's/.*"pipeline_id":"\([^"]*\)".*/\1/p')"
if [[ -z "${pipeline_id:-}" ]]; then
  echo "ERROR: pipeline_id is empty"
  exit 2
fi
echo "pipeline_id=$pipeline_id"
echo

echo "== create stage #1 (New) =="
st1_json="$(curl -sS -X POST "$BASE/api/stages" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"New\",\"sort_order\":10,\"is_won\":false,\"is_lost\":false}")"
echo "$st1_json"
stage1_id="$(printf '%s' "$st1_json" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
if [[ -z "${stage1_id:-}" ]]; then
  echo "ERROR: stage1_id is empty"
  exit 2
fi
echo "stage1_id=$stage1_id"
echo

echo "== create stage #2 (Won) =="
st2_json="$(curl -sS -X POST "$BASE/api/stages" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"Won\",\"sort_order\":99,\"is_won\":true,\"is_lost\":false}")"
echo "$st2_json"
stage2_id="$(printf '%s' "$st2_json" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
if [[ -z "${stage2_id:-}" ]]; then
  echo "ERROR: stage2_id is empty"
  exit 2
fi
echo "stage2_id=$stage2_id"
echo

echo "== create deal =="
deal_json="$(curl -sS -X POST "$BASE/api/deals" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"title\":\"Deal $ts\",\"amount\":\"1000.00\",\"currency\":\"USD\",\"company_id\":null,\"contact_id\":null,\"pipeline_id\":\"$pipeline_id\",\"stage_id\":\"$stage1_id\"}")"
echo "$deal_json"
deal_id="$(printf '%s' "$deal_json" | sed -n 's/.*"deal_id":"\([^"]*\)".*/\1/p')"
if [[ -z "${deal_id:-}" ]]; then
  echo "ERROR: deal_id is empty"
  exit 2
fi
echo "deal_id=$deal_id"
echo

echo "== list deals (limit=10) =="
curl -sS "$BASE/api/deals?limit=10" -H "Authorization: Bearer $token" ; echo
echo

echo "== move deal to Won (PATCH) =="
curl -sS -X PATCH "$BASE/api/deals/$deal_id" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"stage_id\":\"$stage2_id\"}" ; echo
echo

echo "== list deals after move (limit=10) =="
curl -sS "$BASE/api/deals?limit=10" -H "Authorization: Bearer $token" ; echo
echo
