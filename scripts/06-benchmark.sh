#!/bin/bash
set -euo pipefail

MODE="smoke"
while [[ $# -gt 0 ]]; do
  case $1 in
    --code-benchmark)
      MODE="code"
      shift
      ;;
    --integration)
      MODE="integration"
      shift
      ;;
    *)
      echo "Unknown flag $1" >&2
      exit 1
      ;;
  esac
done

case $MODE in
  smoke)
    echo "Running smoke benchmark via gateway"
    curl -fsS http://localhost:8080/v1/proxy \
      -H "Content-Type: application/json" \
      -d '{"task":"chat","payload":{"messages":[{"role":"user","content":"Hello"}]}}'
    ;;
  code)
    echo "Running code benchmark placeholder"
    curl -fsS http://localhost:8080/v1/proxy \
      -H "Content-Type: application/json" \
      -d '{"task":"code","context_tokens":4096,"payload":{"prompt":"Write a fibonacci function in python"}}'
    ;;
  integration)
    echo "Running integration benchmark placeholder"
    curl -fsS http://localhost:8080/v1/proxy \
      -H "Content-Type: application/json" \
      -d '{"task":"chat","complexity":0.9,"payload":{"messages":[{"role":"user","content":"Explain INT4 quantization"}]}}'
    ;;
  *)
    echo "Unsupported benchmark mode $MODE" >&2
    exit 1
    ;;
esac
