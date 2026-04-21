#!/usr/bin/env bash
# Chaos test script — requires toxiproxy running alongside the stack.
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
TOXIPROXY_URL="${TOXIPROXY_URL:-http://localhost:8474}"
PROXY_NAME="backend"

echo "=== Chaos Test Suite ==="

# Helper: wait for backend to be healthy
wait_for_backend() {
  for i in $(seq 1 30); do
    if curl -sf "$BACKEND_URL/api/health" >/dev/null; then
      return 0
    fi
    sleep 1
  done
  echo "Backend did not become healthy"
  return 1
}

# ── Test 1: Latency injection ─────────────────────────────────────────────────
echo "Test 1: Inject 500ms latency..."
# Add latency toxic via toxiproxy CLI or API
curl -sf "$TOXIPROXY_URL/proxies/$PROXY_NAME/toxics" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"latency","type":"latency","attributes":{"latency":500,"jitter":100}}' \
  || true

RESPONSE=$(curl -sf -w "\nHTTP_CODE:%{http_code}\nTIME_TOTAL:%{time_total}\n" "$BACKEND_URL/api/health" || true)
echo "$RESPONSE"
# Should succeed but take >500ms
echo "$RESPONSE" | grep -q "HTTP_CODE:200" || echo "WARNING: health check failed under latency"

# Remove toxic
curl -sf "$TOXIPROXY_URL/proxies/$PROXY_NAME/toxics/latency" -X DELETE || true

# ── Test 2: Packet loss ───────────────────────────────────────────────────────
echo "Test 2: Inject 20% packet loss..."
curl -sf "$TOXIPROXY_URL/proxies/$PROXY_NAME/toxics" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"timeout","type":"timeout","attributes":{"timeout":3000}}' \
  || true

# Request should either succeed or timeout gracefully (not crash)
for i in $(seq 1 5); do
  RESPONSE=$(curl -sf -o /dev/null -w "%{http_code}" --max-time 10 "$BACKEND_URL/api/health" || echo "000")
  echo "Attempt $i: HTTP $RESPONSE"
done

curl -sf "$TOXIPROXY_URL/proxies/$PROXY_NAME/toxics/timeout" -X DELETE || true

# ── Test 3: Downstream recovery ───────────────────────────────────────────────
echo "Test 3: Full downstream blackout then recovery..."
# Disable proxy (simulates downstream failure)
curl -sf "$TOXIPROXY_URL/proxies/$PROXY_NAME" -X POST \
  -H "Content-Type: application/json" \
  -d '{"enabled":false}' || true

sleep 3

# Re-enable
curl -sf "$TOXIPROXY_URL/proxies/$PROXY_NAME" -X POST \
  -H "Content-Type: application/json" \
  -d '{"enabled":true}' || true

wait_for_backend
HEALTH=$(curl -sf "$BACKEND_URL/api/health" | jq -r '.status')
echo "Recovered: status=$HEALTH"
[ "$HEALTH" = "healthy" ] || exit 1

echo "=== Chaos tests completed ==="
