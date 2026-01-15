#!/usr/bin/env bash
set -euo pipefail

PORT="${GATEWAY_PORT:-8088}"

wait_url() {
  local url="$1"
  local tries="${2:-60}"
  local i=1
  while [ "$i" -le "$tries" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "✅ OK: $url"
      return 0
    fi
    i=$((i+1))
    sleep 1
  done
  echo "❌ Timeout waiting for: $url"
  return 1
}

echo "==> Waiting gateway..."
wait_url "http://localhost:${PORT}/health" 60

echo "==> Waiting core via gateway..."
wait_url "http://localhost:${PORT}/api/health" 120

echo "==> Waiting content via gateway..."
wait_url "http://localhost:${PORT}/content/health" 120

echo
curl -fsS "http://localhost:${PORT}/health" | cat; echo
curl -fsS "http://localhost:${PORT}/api/health" | cat; echo
curl -fsS "http://localhost:${PORT}/content/health" | cat; echo

echo "✅ Smoke OK"
