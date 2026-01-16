#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8088}"

echo "== health =="
curl -fsS "${BASE_URL}/api/health"
echo -e "\n"

echo "== version =="
curl -fsS "${BASE_URL}/api/version"
echo -e "\n"

echo "== bootstrap =="
curl -fsS -X POST "${BASE_URL}/api/bootstrap"
echo -e "\n\n"

echo "== login =="
login_json="$(curl -fsS -X POST "${BASE_URL}/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
echo "${login_json}"
echo -e "\n"

token="$(python -c 'import json,sys; print(json.loads(sys.stdin.read())["access_token"])' <<<"${login_json}")"

echo "token=${token}"
echo -e "\n"

echo "== whoami =="
curl -fsS "${BASE_URL}/api/auth/whoami" -H "Authorization: Bearer ${token}"
echo -e "\n"
