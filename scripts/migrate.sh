#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d postgres
docker compose up -d --build core

echo "== waiting for alembic inside nextcrm-core (pip install may still be running) =="
found="0"
for i in $(seq 1 90); do
  if docker exec -i nextcrm-core sh -lc 'command -v alembic >/dev/null 2>&1'; then
    found="1"
    break
  fi
  sleep 1
done

if [ "${found}" != "1" ]; then
  echo "ERROR: alembic not found in nextcrm-core PATH (requirements not installed?)"
  docker logs nextcrm-core --tail 200 || true
  exit 1
fi

docker exec -i nextcrm-core sh -lc 'alembic upgrade head'
echo "✅ migrations OK"
