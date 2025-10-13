#!/bin/bash
set -euo pipefail

MODEL_CONFIG=${MODEL_CONFIG:-/app/models.yaml}
PORT=${VLLM_OPENAI_PORT:-8000}
HF_HOME=${HF_HOME:-/models/hf-cache}

if [[ ! -f "$MODEL_CONFIG" ]]; then
  echo "Model config $MODEL_CONFIG not found" >&2
  exit 1
fi

DEFAULT_MODEL=${DEFAULT_MODEL:-qwen3_8b}

read -r MODEL_REPO MODEL_MAX_LEN <<EOF
$(python3 - <<'PY'
import os, sys, yaml
config_path = os.environ.get("MODEL_CONFIG", "/app/models.yaml")
default_model = os.environ.get("DEFAULT_MODEL", "qwen3_8b")
with open(config_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
try:
    model_cfg = data["models"][default_model]
except KeyError as exc:
    print(f"Missing default model {default_model} in {config_path}", file=sys.stderr)
    sys.exit(1)
print(model_cfg["repository"], model_cfg.get("max_model_len", 8192))
PY
)
EOF

exec python3 -m vllm.entrypoints.openai.api_server \
  --model "${MODEL_REPO}" \
  --download-dir "$HF_HOME" \
  --tensor-parallel-size 1 \
  --host 0.0.0.0 \
  --port "$PORT" \
  --quantization awq \
  --max-model-len "${MODEL_MAX_LEN}"
