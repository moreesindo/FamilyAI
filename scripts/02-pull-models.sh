#!/bin/bash
set -euo pipefail

CONFIG_PATH=${1:-vllm/models.yaml}

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Config $CONFIG_PATH not found" >&2
  exit 1
fi

ABS_CONFIG=$(python3 -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$CONFIG_PATH")
DEFAULT_CONFIG=$(python3 -c 'import os; print(os.path.realpath("vllm/models.yaml"))')

if command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_BIN="docker-compose"
elif command -v docker >/dev/null 2>&1; then
  COMPOSE_BIN="docker compose"
else
  echo "docker compose is required to pull models via container" >&2
  exit 1
fi

MODEL_CONFIG_ENV="/app/models/models.yaml"
EXTRA_VOLUME=()

if [[ "$ABS_CONFIG" != "$DEFAULT_CONFIG" ]]; then
  MODEL_CONFIG_ENV="/tmp/models.yaml"
  EXTRA_VOLUME=(-v "$ABS_CONFIG:$MODEL_CONFIG_ENV:ro")
fi

CMD=("$COMPOSE_BIN" "run" "--rm")
CMD+=("-e" "MODEL_CONFIG_PATH=$MODEL_CONFIG_ENV")
CMD+=("-e" "HF_HOME=/models/hf-cache")
if [[ -n "${HUGGINGFACEHUB_API_TOKEN:-}" ]]; then
  CMD+=("-e" "HUGGINGFACEHUB_API_TOKEN=$HUGGINGFACEHUB_API_TOKEN")
fi
CMD+=("${EXTRA_VOLUME[@]}")
CMD+=("vllm" "python3" "-")

printf 'Using containerised downloader via service "vllm"\n'

"${CMD[@]}" <<'PY'
import os
import sys

import yaml
from huggingface_hub import snapshot_download

config_path = os.environ.get("MODEL_CONFIG_PATH", "/app/models/models.yaml")
hf_home = os.environ.get("HF_HOME", "/models/hf-cache")
token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if not os.path.exists(config_path):
    print(f"Config file {config_path} not present inside container", file=sys.stderr)
    sys.exit(1)

with open(config_path, "r", encoding="utf-8") as handle:
    config = yaml.safe_load(handle) or {}

models = config.get("models", {})
if not models:
    print("No models declared in config", file=sys.stderr)
    sys.exit(1)

repos = {details.get("repository") for details in models.values() if details.get("repository")}
if not repos:
    print("No repositories with 'repository' key found in config", file=sys.stderr)
    sys.exit(1)

for repo in sorted(repos):
    print(f"Downloading {repo} into {hf_home}")
    snapshot_download(
        repo_id=repo,
        cache_dir=hf_home,
        token=token,
        resume_download=True,
        local_files_only=False,
    )
PY
