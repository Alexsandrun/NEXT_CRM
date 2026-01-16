#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE:-http://localhost:8088}"

echo "== bootstrap ==" && curl -sS -X POST "$BASE/api/bootstrap" && echo

echo "== login =="
login_json="$(curl -sS -X POST "$BASE/api/auth/login" -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
echo "$login_json"
token="$(printf '%s' "$login_json" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
echo "token=$token"
echo

echo "== create pipeline =="
pl="$(curl -sS -X POST "$BASE/api/pipelines" -H "Authorization: Bearer $token" -H 'Content-Type: application/json' \
  -d '{"name":"Sales pipeline"}')"
echo "$pl"
pipeline_id="$(printf '%s' "$pl" | sed -n 's/.*"pipeline_id":"\([^"]*\)".*/\1/p')"
echo "pipeline_id=$pipeline_id"
echo

echo "== create stages =="
st1="$(curl -sS -X POST "$BASE/api/pipelines/$pipeline_id/stages" -H "Authorization: Bearer $token" -H 'Content-Type: application/json' \
  -d '{"name":"Lead","sort_order":1,"is_won":false,"is_lost":false}')"
echo "$st1"
stage1_id="$(printf '%s' "$st1" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
echo "stage1_id=$stage1_id"
echo

st2="$(curl -sS -X POST "$BASE/api/pipelines/$pipeline_id/stages" -H "Authorization: Bearer $token" -H 'Content-Type: application/json' \
  -d '{"name":"Won","sort_order":2,"is_won":true,"is_lost":false}')"
echo "$st2"
stage2_id="$(printf '%s' "$st2" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
echo "stage2_id=$stage2_id"
echo

echo "== create deal =="
deal="$(curl -sS -X POST "$BASE/api/deals" -H "Authorization: Bearer $token" -H 'Content-Type: application/json' \
  -d "{\"title\":\"First deal\",\"amount\":1000,\"currency\":\"USD\",\"pipeline_id\":\"$pipeline_id\",\"stage_id\":\"$stage1_id\"}")"
echo "$deal"
deal_id="$(printf '%s' "$deal" | sed -n 's/.*"deal_id":"\([^"]*\)".*/\1/p')"
echo "deal_id=$deal_id"
echo

echo "== list deals =="
curl -sS "$BASE/api/deals?limit=10" -H "Authorization: Bearer $token" && echo
