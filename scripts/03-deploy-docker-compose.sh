#!/bin/bash
set -euo pipefail

export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

if ! command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN="docker compose"
else
  COMPOSE_BIN="docker-compose"
fi

# ghcr.io rate-limits anonymous pulls. Allow supplying credentials through
# GHCR_USERNAME/GHCR_TOKEN to authenticate before the build starts so
# docker-compose can access jetson-containers images without failing.
if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
  echo "Logging into ghcr.io registry"
  # shellcheck disable=SC2005
  if ! echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USERNAME}" --password-stdin; then
    echo "Failed to authenticate to ghcr.io" >&2
    exit 1
  fi
fi

$COMPOSE_BIN -f docker-compose.yml up --build -d
