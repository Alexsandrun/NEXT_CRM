#!/usr/bin/env bash
set -euo pipefail

# Simulate core failure and verify gateway response
BASE="${BASE:-http://localhost:8088}"

echo "Stopping core..."
docker compose stop core

sleep 2

echo "Requesting via gateway ($BASE/api/health) while core is stopped..."
status=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)
echo "Gateway returned HTTP $status"

if [[ "$status" -ne 200 ]]; then
  echo "OK: Gateway indicates failure when core is down (status $status)"
else
  echo "WARN: Gateway returned 200 while core stopped (status $status)"
fi

echo "Starting core..."
docker compose start core

# Wait for core to become healthy (check container health status)
echo "Waiting for core to become healthy (up to 60s)"
for i in {1..30}; do
  hc=$(docker inspect --format='{{.State.Health.Status}}' nextcrm-core 2>/dev/null || true)
  if [[ "$hc" == "healthy" ]]; then
    echo "Core container is healthy"
    break
  fi
  echo -n "."
  sleep 2
done
echo

# Final gateway check
status2=$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)
echo "Gateway returned HTTP $status2 after core restart"

if [[ "$status2" -eq 200 ]]; then
  echo "OK: Gateway recovered after core restart"
  exit 0
else
  echo "FAIL: Gateway still failing after core restart (status $status2)"
  echo "Tip: if you rebuilt core (container recreated), restart gateway to refresh DNS:"
  echo "  docker compose restart gateway"
  exit 2
fi
