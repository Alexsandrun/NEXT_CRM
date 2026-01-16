#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8088}"

echo "== health =="
curl -sS "$BASE/api/health"; echo; echo

echo "== version =="
curl -sS "$BASE/api/version"; echo; echo

echo "== bootstrap =="
BOOTSTRAP="$(curl -sS -X POST "$BASE/api/bootstrap")"
echo "$BOOTSTRAP"; echo; echo

echo "== login =="
LOGIN="$(curl -sS -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
echo "$LOGIN"; echo; echo

TOKEN="$(printf '%s' "$LOGIN" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')"
echo "token=$TOKEN"; echo; echo

echo "== whoami =="
curl -sS "$BASE/api/auth/whoami" -H "Authorization: Bearer $TOKEN"; echo
