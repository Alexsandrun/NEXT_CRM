#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8088}"

echo "== bootstrap =="
curl -sS -X POST "$BASE/api/bootstrap" ; echo

echo "== login =="
login_json="$(curl -sS -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
echo "$login_json"

token="$(printf '%s' "$login_json" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
echo "token=$token"
echo

echo "== create contact =="
create_json="$(curl -sS -X POST "$BASE/api/contacts" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d '{"name":"Alice Example","email":"alice@example.com","phone":"+380501234567"}')"
echo "$create_json"

contact_id="$(printf '%s' "$create_json" | sed -n 's/.*"contact_id":"\([^"]*\)".*/\1/p')"
echo "contact_id=$contact_id"
echo

echo "== list contacts =="
curl -sS "$BASE/api/contacts?limit=10" -H "Authorization: Bearer $token" ; echo
echo

echo "== get contact =="
curl -sS "$BASE/api/contacts/$contact_id" -H "Authorization: Bearer $token" ; echo
echo

echo "== patch contact =="
curl -sS -X PATCH "$BASE/api/contacts/$contact_id" \
  -H "Authorization: Bearer $token" \
  -H 'Content-Type: application/json' \
  -d '{"phone":"+380509999999"}' ; echo
echo

echo "== delete contact =="
curl -sS -X DELETE "$BASE/api/contacts/$contact_id" -H "Authorization: Bearer $token" ; echo
echo
