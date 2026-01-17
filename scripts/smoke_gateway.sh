#!/usr/bin/env bash
set -Eeuo pipefail

# включи TRACE=1 если нужен подробный трейс
if [[ "${TRACE:-0}" == "1" ]]; then
  set -x
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

BASE="${BASE:-http://127.0.0.1:8088}"
TENANT="${TENANT:-demo}"
EMAIL="${EMAIL:-admin@demo.local}"
PASS="${PASS:-admin123}"

die() { echo "ERROR: $*" >&2; exit 1; }

dump_on_err() {
  local code=$?
  echo >&2
  echo "ERROR: exit=$code line=${BASH_LINENO[0]} cmd: $BASH_COMMAND" >&2
  echo "== docker compose ps ==" >&2
  docker compose ps >&2 || true
  echo "== compose logs (tail 200 each) ==" >&2
  docker compose logs --no-color --tail=200 gateway >&2 || true
  docker compose logs --no-color --tail=200 core >&2 || true
  docker compose logs --no-color --tail=200 content >&2 || true
  exit "$code"
}
trap dump_on_err ERR

curl_json() {
  local method="$1"; local url="$2"; shift 2
  local data=""
  if [[ "${1:-}" == "--data" ]]; then
    data="$2"; shift 2
  fi

  local out http
  out="$(mktemp)"

  if [[ -n "$data" ]]; then
    http="$(curl -sS -o "$out" -w "%{http_code}" \
      --connect-timeout 2 --max-time 15 --retry 3 --retry-all-errors --retry-delay 1 \
      -X "$method" "$url" -H 'Content-Type: application/json' -d "$data" "$@" || true)"
  else
    http="$(curl -sS -o "$out" -w "%{http_code}" \
      --connect-timeout 2 --max-time 15 --retry 3 --retry-all-errors --retry-delay 1 \
      -X "$method" "$url" "$@" || true)"
  fi

  if [[ "$http" != 2* ]]; then
    echo "HTTP $http for $method $url" >&2
    echo "--- response body ---" >&2
    cat "$out" >&2 || true
    rm -f "$out"
    return 1
  fi

  cat "$out"
  rm -f "$out"
}

command -v python3 >/dev/null 2>&1 || die "python3 not found (required for JSON parsing)"

echo "== up services =="
docker compose up -d --build core content gateway

echo "== wait /api/health =="
for i in {1..120}; do
  code="$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)"
  if [[ "$code" == "200" ]]; then
    echo "health OK"
    break
  fi
  echo "wait health... ($i) http=$code"
  sleep 1
  [[ "$i" == "120" ]] && die "gateway /api/health didn't become 200"
done

echo "== openapi has board endpoint =="
for i in {1..60}; do
  code="$(curl -sS -o /tmp/openapi.json -w "%{http_code}" "$BASE/api/openapi.json" || true)"
  [[ "$code" == "200" ]] && break
  echo "wait openapi... ($i) http=$code"
  sleep 1
  [[ "$i" == "60" ]] && die "openapi didn't become 200"
done
grep -q '"/pipelines/{pipeline_id}/board"' /tmp/openapi.json || die "board endpoint not in openapi"
echo "openapi OK"

echo "== bootstrap (idempotent) =="
curl -sS -X POST "$BASE/api/bootstrap" -H 'Content-Type: application/json' >/dev/null || true

echo "== login =="
login_json="$(curl_json POST "$BASE/api/auth/login" --data "{\"tenant\":\"$TENANT\",\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")"
TOKEN="$(printf '%s' "$login_json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))')"
[[ -n "$TOKEN" ]] || die "login did not return access_token; body: $login_json"
auth=(-H "Authorization: Bearer $TOKEN")

echo "== create pipeline =="
ts="$(date +%s)"
pipe_json="$(curl_json POST "$BASE/api/pipelines" --data "{\"name\":\"CI Sales $ts\"}" "${auth[@]}")"
PIPELINE_ID="$(printf '%s' "$pipe_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["pipeline_id"])')"
echo "pipeline_id=$PIPELINE_ID"

echo "== create stages =="
st1_json="$(curl_json POST "$BASE/api/stages" --data "{\"pipeline_id\":\"$PIPELINE_ID\",\"name\":\"New\",\"sort_order\":10}" "${auth[@]}")"
ST1="$(printf '%s' "$st1_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["stage_id"])')"

st2_json="$(curl_json POST "$BASE/api/stages" --data "{\"pipeline_id\":\"$PIPELINE_ID\",\"name\":\"Won\",\"sort_order\":99,\"is_won\":true}" "${auth[@]}")"
ST2="$(printf '%s' "$st2_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["stage_id"])')"

echo "== create deal =="
deal_json="$(curl_json POST "$BASE/api/deals" --data "{\"title\":\"Deal CI $ts\",\"amount\":1000,\"pipeline_id\":\"$PIPELINE_ID\",\"stage_id\":\"$ST1\"}" "${auth[@]}")"
DEAL="$(printf '%s' "$deal_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["deal_id"])')"

echo "== board request (include_empty=true) =="
board_json="$(curl_json GET "$BASE/api/pipelines/$PIPELINE_ID/board?include_empty=true" "${auth[@]}")"
[[ -n "$board_json" ]] || die "board response is empty"
printf '%s' "$board_json" | python3 -c 'import json,sys; b=json.load(sys.stdin); assert "columns" in b, "no columns"; assert len(b["columns"])>=2, "expected >=2 columns"; print("board OK, columns=", len(b["columns"]))'

echo "== move deal to Won (PATCH) =="
curl_json PATCH "$BASE/api/deals/$DEAL" --data "{\"stage_id\":\"$ST2\"}" "${auth[@]}" >/dev/null

echo "== board after move =="
board2="$(curl_json GET "$BASE/api/pipelines/$PIPELINE_ID/board?include_empty=true" "${auth[@]}")"
[[ -n "$board2" ]] || die "board(after move) response is empty"
printf '%s' "$board2" | DEAL_ID="$DEAL" WON_ID="$ST2" python3 -c '
import os,json,sys
b=json.load(sys.stdin)
deal_id=os.environ["DEAL_ID"]
won_id=os.environ["WON_ID"]
for col in b.get("columns", []):
    if col.get("stage", {}).get("stage_id") == won_id:
        if any(d.get("deal_id") == deal_id for d in col.get("deals", [])):
            print("move OK")
            raise SystemExit(0)
raise SystemExit("moved deal not found in Won column")
'

echo "ALL SMOKE CHECKS PASSED"
