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

echo "== create company =="
co_name="ACME LLC $(date +%s)"
co_json="$(curl -sS -X POST "$BASE/api/companies" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"$co_name\",\"domain\":\"acme.com\"}")"
echo "$co_json"
company_id="$(printf '%s' "$co_json" | sed -n 's/.*"company_id":"\([^"]*\)".*/\1/p')"
echo "company_id=$company_id"
echo

echo "== create contact linked to company =="
ct_json="$(curl -sS -X POST "$BASE/api/contacts" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"Bob\",\"email\":\"bob@acme.com\",\"company_id\":\"$company_id\"}")"
echo "$ct_json"
contact_id="$(printf '%s' "$ct_json" | sed -n 's/.*"contact_id":"\([^"]*\)".*/\1/p')"
echo "contact_id=$contact_id"
echo

echo "== list companies =="
curl -sS "$BASE/api/companies?limit=10" -H "Authorization: Bearer $token"
echo
echo

echo "== list contacts =="
curl -sS "$BASE/api/contacts?limit=10" -H "Authorization: Bearer $token"
echo
