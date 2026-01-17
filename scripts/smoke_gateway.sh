 #!/usr/bin/env bash
-set -Eeuo pipefail
+set -Eeuo pipefail

 ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
 cd "$ROOT"
@@ -8,6 +8,12 @@ BASE="${BASE:-http://127.0.0.1:8088}"
 TENANT="${TENANT:-demo}"
 EMAIL="${EMAIL:-admin@demo.local}"
 PASS="${PASS:-admin123}"
+
+# curl defaults (avoid hangs in CI)
+CURL_CONNECT_TIMEOUT="${CURL_CONNECT_TIMEOUT:-3}"
+CURL_MAX_TIME="${CURL_MAX_TIME:-15}"
+
+curl_common=(-sS --connect-timeout "$CURL_CONNECT_TIMEOUT" --max-time "$CURL_MAX_TIME")

 die() { echo "ERROR: $*" >&2; exit 1; }

@@ -33,10 +39,10 @@ curl_json() {

   local out http
   out="$(mktemp)"
   if [[ -n "$data" ]]; then
-    http="$(curl -sS -o "$out" -w "%{http_code}" -X "$method" "$url" \
+    http="$(curl "${curl_common[@]}" -o "$out" -w "%{http_code}" -X "$method" "$url" \
       -H 'Content-Type: application/json' -d "$data" "$@" || true)"
   else
-    http="$(curl -sS -o "$out" -w "%{http_code}" -X "$method" "$url" "$@" || true)"
+    http="$(curl "${curl_common[@]}" -o "$out" -w "%{http_code}" -X "$method" "$url" "$@" || true)"
   fi

   if [[ "$http" != 2* ]]; then
@@ -55,23 +61,6 @@ curl_json() {
   rm -f "$out"
 }

-need_python() {
-  command -v python3 >/dev/null 2>&1 || die "python3 not found (required for JSON parsing)"
-}
-
-json_get() {
-  # usage: json_get '<json>' 'key'
-  python3 - <<'PY'
-import json,sys
-j=json.loads(sys.stdin.read())
-key=sys.argv[1]
-print(j.get(key,""))
-PY
-}
-
-need_python
+command -v python3 >/dev/null 2>&1 || die "python3 not found (required for JSON parsing)"

 echo "== up services =="
 docker compose up -d --build core content gateway

 echo "== wait /api/health =="
 for i in {1..120}; do
-  code="$(curl -sS -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)"
+  code="$(curl "${curl_common[@]}" -o /dev/null -w "%{http_code}" "$BASE/api/health" || true)"
   [[ "$code" == "200" ]] && break
   echo "wait health... ($i) http=$code"
   sleep 1
   [[ "$i" == "120" ]] && die "gateway /api/health didn't become 200"
 done
 echo "health OK"

+echo "== wait /api/openapi.json (board must be present) =="
+openapi_tmp="$(mktemp)"
+for i in {1..120}; do
+  code="$(curl "${curl_common[@]}" -o "$openapi_tmp" -w "%{http_code}" "$BASE/api/openapi.json" || true)"
+  if [[ "$code" == "200" ]] && grep -q '"/pipelines/{pipeline_id}/board"' "$openapi_tmp"; then
+    echo "openapi OK"
+    break
+  fi
+  echo "wait openapi... ($i) http=$code"
+  sleep 1
+  [[ "$i" == "120" ]] && { echo "openapi body:"; head -c 1200 "$openapi_tmp" || true; die "openapi didn't become ready or board not found"; }
+done
+rm -f "$openapi_tmp"
+
 echo "== bootstrap (idempotent) =="
-curl -sS -X POST "$BASE/api/bootstrap" -H 'Content-Type: application/json' >/dev/null || true
+boot_tmp="$(mktemp)"
+boot_code="$(curl "${curl_common[@]}" -o "$boot_tmp" -w "%{http_code}" -X POST "$BASE/api/bootstrap" -H 'Content-Type: application/json' || true)"
+if [[ "$boot_code" != "200" && "$boot_code" != "400" && "$boot_code" != "409" ]]; then
+  echo "bootstrap http=$boot_code"
+  cat "$boot_tmp" || true
+  rm -f "$boot_tmp"
+  die "bootstrap failed"
+fi
+rm -f "$boot_tmp"

 echo "== login =="
 login_json="$(curl_json POST "$BASE/api/auth/login" --data "{\"tenant\":\"$TENANT\",\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")"
 TOKEN="$(printf '%s' "$login_json" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("access_token",""))')"
 [[ -n "$TOKEN" ]] || die "login did not return access_token; body: $login_json"
 auth=(-H "Authorization: Bearer $TOKEN")
@@ -106,7 +95,7 @@ echo "== create deal =="
 deal_json="$(curl_json POST "$BASE/api/deals" --data "{\"title\":\"Deal CI $ts\",\"amount\":1000,\"pipeline_id\":\"$PIPELINE_ID\",\"stage_id\":\"$ST1\"}" "${auth[@]}")"
 DEAL="$(printf '%s' "$deal_json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["deal_id"])')"

 echo "== board request (include_empty=true) =="
 board_json="$(curl_json GET "$BASE/api/pipelines/$PIPELINE_ID/board?include_empty=true" "${auth[@]}")"
 printf '%s' "$board_json" | python3 - <<PY
 import json,sys
 b=json.load(sys.stdin)
 assert "columns" in b, "no 'columns' in board"
 assert len(b["columns"]) >= 2, "expected at least 2 columns"
 print("board OK, columns=", len(b["columns"]))
 PY

 echo "== move deal to Won (PATCH) =="
 curl_json PATCH "$BASE/api/deals/$DEAL" --data "{\"stage_id\":\"$ST2\"}" "${auth[@]}" >/dev/null

 echo "== board after move =="
-board2="$(curl_json GET "$BASE/api/pipelines/$PIPELINE_ID/board?include_empty=true" "${auth[@]}")"
-printf '%s' "$board2" | python3 - <<PY
-import json,sys
-b=json.load(sys.stdin)
-deal_id = "$DEAL"
-won_id = "$ST2"
-for col in b.get("columns",[]):
-  if col.get("stage",{}).get("stage_id")==won_id:
-    if any(d.get("deal_id")==deal_id for d in col.get("deals",[])):
-      print("move OK")
-      raise SystemExit(0)
-raise SystemExit("moved deal not found in Won column")
-PY
+ok=0
+for i in {1..20}; do
+  board2="$(curl_json GET "$BASE/api/pipelines/$PIPELINE_ID/board?include_empty=true" "${auth[@]}")"
+  if printf '%s' "$board2" | python3 - <<PY
+import json,sys
+b=json.load(sys.stdin)
+deal_id = "$DEAL"
+won_id = "$ST2"
+for col in b.get("columns",[]):
+  if col.get("stage",{}).get("stage_id")==won_id:
+    if any(d.get("deal_id")==deal_id for d in col.get("deals",[])):
+      print("move OK")
+      raise SystemExit(0)
+raise SystemExit(1)
+PY
+  then
+    ok=1
+    break
+  fi
+  echo "wait move propagation... ($i)"
+  sleep 0.5
+done
+[[ "$ok" == "1" ]] || die "moved deal not found in Won column after retries"

 echo "ALL SMOKE CHECKS PASSED"
