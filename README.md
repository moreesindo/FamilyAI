# FamilyAI

FamilyAI delivers family-focused AI services (code assistance, chat, vision, and speech) optimized for NVIDIA Jetson Thor. Every component ships as an ARM64 container and is orchestrated through a control plane that manages model inventory, downloads, and smart routing.

## Service Topology

| Service        | Port | Purpose |
|----------------|------|---------|
| `gateway`      | 8080 | Unified OpenAI-style API with dynamic routing |
| `control-plane`| 9000 | Model catalog, download scheduler, recommendation engine |
| `vllm`         | n/a  | INT4 LLM serving for local Qwen models |
| `vision`       | n/a  | Vision metadata extractor (Qwen2-VL adapter) |
| `whisper`      | n/a  | ASR microservice wrapping Whisper Small |
| `piper`        | n/a  | TTS microservice with Piper voice packs |
| `web-ui`       | 3000 | Open WebUI front door for family members |
| `admin-ui`     | 8081 | Static dashboard stub targeting the control plane APIs |

Only Jetson Thor servers should run the stack. Use development machines for authoring code and manifests; build and execute containers on the Jetson host.

## Workflow

```bash
# 1. Prepare model cache locally on Jetson (runs inside vLLM container)
HUGGINGFACEHUB_API_TOKEN=<token> ./scripts/02-pull-models.sh  # token optional for public models

# 2. Launch full stack (Jetson only)
./scripts/03-deploy-docker-compose.sh

# 3. Verify health (requires docker compose access)
./scripts/05-health-check.sh

# 4. Interact with the control plane
CONTROL_PLANE_URL=http://localhost:9000 ./scripts/07-control-plane-cli.sh list
```

For production, apply manifests under `k3s/` to the on-device K3s cluster. Contributor guidance lives in `AGENTS.md`; operational playbooks are in `docs/05-troubleshooting.md`.
