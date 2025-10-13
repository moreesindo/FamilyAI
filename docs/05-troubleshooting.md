# Troubleshooting Guide

## Common Failures

### Containers fail to start on Jetson Thor
- Run `sudo systemctl restart docker` to refresh NVIDIA runtime hooks.
- Validate `nvidia-container-runtime` is installed: `which nvidia-container-runtime`.
- Inspect compose logs: `docker compose logs gateway`.

### vLLM Out-Of-Memory
- Confirm only one dense model is loaded at a time using `docker stats`.
- Reduce default model size by setting `DEFAULT_MODEL=qwen3_4b` in the vLLM deployment.
- Re-run `./scripts/02-pull-models.sh` to ensure AWQ weights are available.

### Degraded Whisper Accuracy
- Verify the `MODEL_NAME` matches downloaded checkpoints.
- Check sample rate of audio; resample to 16kHz before upload.
- Restart pod to clear GPU state: `kubectl --context jetson-thor rollout restart deployment/whisper -n familyai`.

### Piper service returns `degraded`
- Ensure voice ONNX bundle exists under `/voices` in the container image.
- Set `VOICE_MODEL` and `VOICE_CONFIG` env vars to explicit paths within the persistent volume.
- Monitor logs for fallback activation: `kubectl logs deployment/piper -n familyai`.

### Gateway 502 Errors
- Confirm downstream service health with `./scripts/05-health-check.sh`.
- Review routing config for typos; apply updates with `kubectl apply -f k3s/gateway-deployment.yaml`.
- Inspect Prometheus alert history for spikes in latency.

### Control Plane Unreachable
- Check `docker compose logs control-plane` for YAML parsing errors.
- Ensure `control-plane/config/models.yaml` contains valid endpoints for every local model.
- The gateway falls back to static routing when the control plane is down; confirm `metadata.source` in API responses.

### Model Download Jobs Never Complete
- Pending jobs create marker files in `control-plane/downloads/`. Clear stale markers before re-queuing.
- Verify outbound network access from Jetson Thor for HuggingFace or OpenRouter endpoints.
- Run `./scripts/07-control-plane-cli.sh list` to confirm model availability and state.
