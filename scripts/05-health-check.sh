#!/bin/bash
set -euo pipefail

EXTERNAL_URLS=(
  "${GATEWAY_HEALTH_URL:-http://localhost:8080/health}"
  "${CONTROL_PLANE_HEALTH_URL:-http://localhost:9000/health}"
)

INTERNAL_ENDPOINTS=(
  "http://vllm:8000/health"
  "http://vision:8300/health"
  "http://whisper:8500/health"
  "http://piper:8600/health"
)

echo "== External endpoints =="
for url in "${EXTERNAL_URLS[@]}"; do
  echo "Checking $url"
  curl -fsS "$url" >/dev/null
  echo "Healthy: $url"
done

echo "== Internal service endpoints (via gateway container) =="
if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN="docker-compose"
elif command -v docker >/dev/null 2>&1; then
  COMPOSE_BIN="docker compose"
else
  echo "docker compose not available; skipping internal health checks" >&2
  exit 0
fi

for endpoint in "${INTERNAL_ENDPOINTS[@]}"; do
  echo "Checking $endpoint"
  $COMPOSE_BIN exec -T gateway curl -fsS "$endpoint" >/dev/null
  echo "Healthy: $endpoint"
done
