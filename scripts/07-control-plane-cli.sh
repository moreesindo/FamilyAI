#!/bin/bash
set -euo pipefail

BASE_URL=${CONTROL_PLANE_URL:-http://localhost:9000}
CMD=${1:-help}
shift || true

usage() {
  cat <<USAGE
Usage: $0 <command> [args]
Commands:
  health                Check control plane health
  list                  List registered models
  recommend <task>      Ask for recommendation (optional flags: --context N --priority MODE --allow-cloud [true|false])
  activate <profile>    Activate routing profile
  download <model_id>   Queue a model download job
USAGE
}

case "$CMD" in
  health)
    curl -fsS "$BASE_URL/health" | jq .
    ;;
  list)
    curl -fsS "$BASE_URL/models" | jq .
    ;;
  recommend)
    TASK=${1:-}
    if [[ -z "$TASK" ]]; then
      echo "Task is required" >&2
      usage
      exit 1
    fi
    shift
    CONTEXT=4096
    PRIORITY="balanced"
    ALLOW_CLOUD=true
    while [[ $# -gt 0 ]]; do
      case $1 in
        --context)
          CONTEXT=$2
          shift 2
          ;;
        --priority)
          PRIORITY=$2
          shift 2
          ;;
        --allow-cloud)
          ALLOW_CLOUD=$2
          shift 2
          ;;
        *)
          echo "Unknown flag $1" >&2
          exit 1
          ;;
      esac
    done
    curl -fsS "$BASE_URL/recommend" \
      -H "Content-Type: application/json" \
      -d "{\"task\": \"$TASK\", \"context_tokens\": $CONTEXT, \"priority\": \"$PRIORITY\", \"allow_cloud\": $ALLOW_CLOUD}" | jq .
    ;;
  activate)
    PROFILE=${1:-}
    if [[ -z "$PROFILE" ]]; then
      echo "Profile name required" >&2
      usage
      exit 1
    fi
    curl -fsS -X POST "$BASE_URL/profiles/$PROFILE/activate" | jq .
    ;;
  download)
    MODEL=${1:-}
    if [[ -z "$MODEL" ]]; then
      echo "Model id required" >&2
      usage
      exit 1
    fi
    curl -fsS -X POST "$BASE_URL/models/$MODEL/download" \
      -H "Content-Type: application/json" \
      -d "{\"model_id\": \"$MODEL\"}" | jq .
    ;;
  help|*)
    usage
    ;;
esac
