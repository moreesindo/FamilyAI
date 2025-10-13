#!/bin/bash
set -euo pipefail

CONFIG=${1:-vllm/models.yaml}
HF_HOME=${HF_HOME:-$HOME/.cache/huggingface}

if [[ ! -f "$CONFIG" ]]; then
  echo "Config $CONFIG not found" >&2
  exit 1
fi

python3 - <<'PY'
import os
import subprocess
import sys
yaml_available = True
try:
    import yaml
except ImportError:
    yaml_available = False

if not yaml_available:
    print("PyYAML is required to parse model config", file=sys.stderr)
    sys.exit(1)

config_path = sys.argv[1]
hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
with open(config_path, "r", encoding="utf-8") as handle:
    config = yaml.safe_load(handle)

models = config.get("models", {})
if not models:
    print("No models declared in config", file=sys.stderr)
    sys.exit(1)

for model in models.values():
    repo = model["repository"]
    print(f"Pulling {repo}...")
    subprocess.run(
        [
            "huggingface-cli",
            "download",
            repo,
            "--cache-dir",
            hf_home,
            "--exclude",
            "*.safetensors",
        ],
        check=False,
    )
PY
"$CONFIG"
