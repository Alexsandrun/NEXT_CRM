#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8088}"

echo "== wait gateway =="
for i in {1..40}; do
  code="$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)"
  [[ "$code" == "200" ]] && { echo "gateway ok"; break; }
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
[[ -z "${token:-}" ]] && { echo "ERROR: token empty"; exit 2; }
echo "token=$token"
echo

ts="$(date +%s)"

echo "== create company =="
co_json="$(curl -sS -X POST "$BASE/api/companies" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"ACME LLC $ts\",\"domain\":\"acme.com\"}")"
echo "$co_json"
company_id="$(printf '%s' "$co_json" | sed -n 's/.*"company_id":"\([^"]*\)".*/\1/p')"
[[ -z "${company_id:-}" ]] && { echo "ERROR: company_id empty"; exit 2; }
echo "company_id=$company_id"
echo

echo "== create contact linked to company =="
ct_json="$(curl -sS -X POST "$BASE/api/contacts" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Bob $ts\",\"email\":\"bob+$ts@acme.com\",\"company_id\":\"$company_id\"}")"
echo "$ct_json"
contact_id="$(printf '%s' "$ct_json" | sed -n 's/.*"contact_id":"\([^"]*\)".*/\1/p')"
[[ -z "${contact_id:-}" ]] && { echo "ERROR: contact_id empty"; exit 2; }
echo "contact_id=$contact_id"
echo

echo "== create pipeline =="
pipe_json="$(curl -sS -X POST "$BASE/api/pipelines" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Sales $ts\"}")"
echo "$pipe_json"
pipeline_id="$(printf '%s' "$pipe_json" | sed -n 's/.*"pipeline_id":"\([^"]*\)".*/\1/p')"
[[ -z "${pipeline_id:-}" ]] && { echo "ERROR: pipeline_id empty"; exit 2; }
echo "pipeline_id=$pipeline_id"
echo

echo "== create stage New =="
st1_json="$(curl -sS -X POST "$BASE/api/stages" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"New\",\"sort_order\":10}")"
echo "$st1_json"
stage1_id="$(printf '%s' "$st1_json" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
[[ -z "${stage1_id:-}" ]] && { echo "ERROR: stage1_id empty"; exit 2; }
echo "stage1_id=$stage1_id"
echo

echo "== create stage Won =="
st2_json="$(curl -sS -X POST "$BASE/api/stages" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"pipeline_id\":\"$pipeline_id\",\"name\":\"Won\",\"sort_order\":99,\"is_won\":true}")"
echo "$st2_json"
stage2_id="$(printf '%s' "$st2_json" | sed -n 's/.*"stage_id":"\([^"]*\)".*/\1/p')"
[[ -z "${stage2_id:-}" ]] && { echo "ERROR: stage2_id empty"; exit 2; }
echo "stage2_id=$stage2_id"
echo

echo "== create deal linked to company+contact =="
deal_json="$(curl -sS -X POST "$BASE/api/deals" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"title\":\"Deal $ts\",\"amount\":\"2500.00\",\"currency\":\"USD\",\"company_id\":\"$company_id\",\"contact_id\":\"$contact_id\",\"pipeline_id\":\"$pipeline_id\",\"stage_id\":\"$stage1_id\"}")"
echo "$deal_json"
deal_id="$(printf '%s' "$deal_json" | sed -n 's/.*"deal_id":"\([^"]*\)".*/\1/p')"
[[ -z "${deal_id:-}" ]] && { echo "ERROR: deal_id empty"; exit 2; }
echo "deal_id=$deal_id"
echo

echo "== list deals for this pipeline =="
curl -sS "$BASE/api/deals?pipeline_id=$pipeline_id&limit=10" -H "Authorization: Bearer $token" ; echo
echo

echo "== move deal to Won =="
curl -sS -X PATCH "$BASE/api/deals/$deal_id" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"stage_id\":\"$stage2_id\"}" ; echo
echo

echo "== list deals for this pipeline after move =="
curl -sS "$BASE/api/deals?pipeline_id=$pipeline_id&limit=10" -H "Authorization: Bearer $token" ; echo
echo
