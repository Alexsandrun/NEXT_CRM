#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8088}"

wait_url() {
  local url="$1"
  local tries="${2:-40}"
  for _ in $(seq 1 "$tries"); do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  echo "❌ timeout waiting for $url" >&2
  return 1
}

echo "== wait gateway =="
# ждём, пока gateway начнёт стабильно отвечать
wait_url "$BASE/health" 40 || true
wait_url "$BASE/api/health" 60

echo
echo "== health =="
curl -sS "$BASE/api/health"
echo

echo
echo "== version =="
curl -sS "$BASE/api/version"
echo

echo
echo "== bootstrap =="
curl -sS -X POST "$BASE/api/bootstrap"
echo

echo
echo "== login =="
login_json="$(curl -sS -X POST "$BASE/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"tenant":"demo","email":"admin@demo.local","password":"admin123"}')"
echo "$login_json"

token="$(printf '%s' "$login_json" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')"
echo
echo "token=$token"

if [[ -z "${token}" ]]; then
  echo "❌ token is empty; login_json was: $login_json" >&2
  exit 1
fi

echo
echo "== whoami =="
curl -sS "$BASE/api/auth/whoami" -H "Authorization: Bearer $token"
echo
