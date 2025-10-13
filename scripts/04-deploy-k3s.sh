#!/bin/bash
set -euo pipefail

K3S_CONTEXT=${K3S_CONTEXT:-jetson-thor}
MANIFEST_DIR=${1:-k3s}

echo "Applying manifests in $MANIFEST_DIR to context $K3S_CONTEXT"
kubectl --context "$K3S_CONTEXT" apply -f "$MANIFEST_DIR"
