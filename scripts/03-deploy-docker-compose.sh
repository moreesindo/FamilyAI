#!/bin/bash
set -euo pipefail

export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

if ! command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN="docker compose"
else
  COMPOSE_BIN="docker-compose"
fi

$COMPOSE_BIN -f docker-compose.yml up --build -d
