## Project Overview

**FamilyAI** is a family-oriented AI service center deployed on NVIDIA Jetson Thor, providing multiple AI services including code assistance, conversational AI, vision understanding, and speech processing for family members.

---

## Core Development Principles

### Primary Requirement: Containerized Deployment on Jetson Thor

**ALL applications in this repository MUST be containerized and deployable on NVIDIA Jetson Thor servers.**

- All applications must run in Docker containers
- All applications must be compatible with NVIDIA Jetson Thor hardware (ARM64 architecture)
- Containerization is mandatory for every service
- Use `jetson-containers` base images when available for optimal performance

### Hardware Specifications

**NVIDIA Jetson Thor**:
- Memory: 128GB LPDDR5X
- GPU Compute: 2070 TFLOPs FP4, 1035 TFLOPs FP8
- CUDA Cores: 2560 + 96 Tensor Cores
- Architecture: Blackwell with native FP4 support

---

## Architecture

### Technology Stack

```yaml
Inference Framework: vLLM (unified for all LLM services)
Quantization: INT4/AWQ (memory optimization)
Container Runtime: Docker with NVIDIA Container Toolkit
Orchestration: K3s (lightweight Kubernetes)
API Gateway: Intelligent routing based on task type
Frontend: Open WebUI
Monitoring: Prometheus + Grafana
```

### Service Architecture

```
┌─────────────────────────────────────────────┐
│         Family Member Access Layer          │
│   (Web UI / Mobile / VS Code / API)         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│       Intelligent Routing Gateway           │
│  (Task-based model selection & routing)     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         K3s Container Orchestration         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│              Service Containers             │
│ ┌─────────────┐ ┌─────────────┐            │
│ │Code Assistant│ │Chat Services│            │
│ │(2 models)   │ │(3 models)   │            │
│ └─────────────┘ └─────────────┘            │
│ ┌─────────────┐ ┌─────────────┐            │
│ │Vision AI    │ │Speech (ASR) │            │
│ └─────────────┘ └─────────────┘            │
│ ┌─────────────┐ ┌─────────────┐            │
│ │Speech (TTS) │ │Web UI       │            │
│ └─────────────┘ └─────────────┘            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│        vLLM Inference Engine Layer          │
│    (INT4 quantization, PagedAttention)      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│           Jetson Thor Hardware              │
│       (128GB RAM, 2070 FP4 TFLOPS)          │
└─────────────────────────────────────────────┘
```

### Control Plane Management Layer

- **Control Plane API (`control-plane/`)**: central catalog for local and cloud models, handling download queues, routing profiles, and cost/latency metadata. Exposes `/recommend` for OpenRouter-style smart selection used by the gateway.
- **Admin UI (`admin-ui/`)**: lightweight static dashboard surfacing control-plane APIs; replace with SPA when design assets are ready.
- **Dynamic Routing**: gateway consults control plane whenever a policy defines `control_plane_profile`. Responses include `metadata.source` (`control-plane` vs `static`) for observability.

---

## Model Selection

### Code Assistant Services (Hot-swappable)

**Traditional Code Tasks**:
- Model: `Qwen/Qwen2.5-Coder-32B-Instruct`
- Parameters: 32B (dense)
- Memory: ~18GB (INT4)
- Use Cases: IDE code completion, function generation, bug fixing, code refactoring
- Performance: Aider 73.7 (GPT-4o level)

**Agentic Workflows**:
- Model: `Qwen/Qwen3-Coder-30B-A3B-Instruct`
- Parameters: 30B total, 3.3B active (MoE)
- Memory: ~15GB (INT4)
- Use Cases: Multi-file refactoring, repository-scale understanding, browser automation, long-context tasks
- Context: 256K native, 1M extended

### Conversational AI Services (Always Running)

**Advanced Reasoning**:
- Model: `Qwen/Qwen3-32B-Instruct`
- Parameters: 32B
- Memory: ~18GB (INT4)
- Performance: Equivalent to Qwen2.5-72B (50% parameter efficiency gain)

**Fast Response**:
- Model: `Qwen/Qwen3-8B-Instruct`
- Parameters: 8B
- Memory: ~4GB (INT4)
- Performance: Equivalent to Qwen2.5-14B
- Speed: ~150-200 tokens/sec on Thor

**Lightweight Interaction**:
- Model: `Qwen/Qwen3-4B-Instruct`
- Parameters: 4B
- Memory: ~2GB (INT4)
- Performance: Equivalent to Qwen2.5-7B
- Speed: ~300-400 tokens/sec on Thor

### Vision Understanding

- Model: `Qwen/Qwen2-VL-7B-Instruct`
- Parameters: 7B
- Memory: ~4GB (INT4)
- Use Cases: Image understanding, visual Q&A, OCR

### Speech Services

**ASR (Automatic Speech Recognition)**:
- Model: `openai/whisper-small`
- Parameters: 244M
- Memory: ~2GB
- Performance: Real-time factor < 0.3

**TTS (Text-to-Speech)**:
- Model: `rhasspy/piper`
- Parameters: <100M
- Memory: ~500MB
- Performance: Real-time synthesis

---

## Resource Allocation

### Memory Budget (INT4 Quantization)

| Service Category | Models | Peak Memory | Typical Memory |
|-----------------|--------|-------------|----------------|
| Code (either)   | 1 model| ~18GB       | ~18GB          |
| Chat (all)      | 3 models| ~24GB      | ~24GB          |
| Vision          | 1 model| ~4GB        | ~4GB           |
| Speech          | 2 models| ~2.5GB     | ~2.5GB         |
| **Total**       |        | **~48GB**   | **~40GB**      |

**Remaining**: ~80GB for batch processing and concurrency

### Expected Performance (Jetson Thor)

| Model | Tokens/sec | Concurrent Users | Response Time |
|-------|-----------|------------------|---------------|
| Qwen2.5-Coder-32B | 50-70 | 3-5 | 2-4s |
| Qwen3-Coder-30B-A3B | 70-90 | 5-8 | 1-3s |
| Qwen3-32B | 50-70 | 5-8 | 2-3s |
| Qwen3-8B | 150-200 | 8-12 | 1-2s |
| Qwen3-4B | 300-400 | 12-15 | <1s |
| Whisper-Small | 10x RT | 10+ | <0.5s |

---

## Development Workflow

### Adding New Services

1. Create service-specific directory under project root
2. Write Dockerfile using `jetson-containers` base images
3. Add service configuration to `docker-compose.yml`
4. Create K3s deployment manifest in `k3s/` directory
5. Update intelligent routing gateway if needed
6. Add health check endpoints
7. Update monitoring configuration

### Model Management

**Control Plane Catalog**:
1. Declare models (local and cloud) in `control-plane/config/models.yaml` with cost, latency, context, and endpoint metadata.
2. Commit matching ConfigMap updates under `k3s/control-plane-deployment.yaml`.
3. Use `CONTROL_PLANE_URL=http://localhost:9000 ./scripts/07-control-plane-cli.sh list` to verify catalog content on Jetson.

**Downloading Models (Jetson only)**:
```bash
# Runs inside the vLLM container; token optional for public repos
HUGGINGFACEHUB_API_TOKEN=<token> ./scripts/02-pull-models.sh
```

Models populate the Docker volume `familyai_model-cache` (mounted at `/models/hf-cache` inside inference containers). Use `docker volume inspect familyai_model-cache` to confirm occupancy or override the cache path via Docker Engine settings if needed.

> Proxy Note: `vllm` builds from `nvcr.io/nvidia/tritonserver:25.08-vllm-python-py3` and sets `HTTP(S)_PROXY=http://127.0.0.1:2526`. Usually you should point it to the Docker bridge IP (e.g., `http://192.168.3.84:2526`) via `PROXY_URL` when building: `PROXY_URL=http://192.168.3.84:2526 docker compose build vllm`. Adjust Compose/K3s envs if your network layout differs.

**Adding New Models**:
1. Extend `control-plane/config/models.yaml` and (if local) `vllm/models.yaml`.
2. Provide service-specific env overrides (e.g., `DEFAULT_MODEL`) under `k3s/`.
3. Update gateway policies in `gateway/config/routing.yaml` to opt-in to control-plane profiles.
4. Apply new manifests to K3s and run `./scripts/05-health-check.sh`.

### Deployment Commands

**Docker Compose** (for development):
```bash
./scripts/03-deploy-docker-compose.sh
```

**K3s** (for production):
```bash
./scripts/04-deploy-k3s.sh
```

**Health Check**:
```bash
./scripts/05-health-check.sh
```

**Performance Benchmark**:
```bash
./scripts/06-benchmark.sh
```

**Control Plane CLI**:
```bash
CONTROL_PLANE_URL=http://localhost:9000 ./scripts/07-control-plane-cli.sh recommend chat --priority quality
```

---

## Intelligent Routing

The routing gateway (`gateway/router.py`) automatically selects the best model based on:

### Code Assistant Routing

**Route to Qwen2.5-Coder-32B** if:
- Task: Code completion, generation, or single-file refactoring
- Context: < 8K tokens
- Priority: Accuracy over speed

**Route to Qwen3-Coder-30B-A3B** if:
- Task: Multi-file analysis, repository understanding
- Context: > 8K tokens or requires long-context
- Priority: Agentic capabilities, browser automation

### Chat Routing

**Route to Qwen3-4B** if:
- Simple Q&A, quick lookups
- Response time critical

**Route to Qwen3-8B** if:
- General conversation, explanations
- Balanced quality and speed

**Route to Qwen3-32B** if:
- Complex reasoning, creative writing
- High-quality response required

---

## Testing

### Unit Tests

Run service-specific tests:
```bash
pytest tests/test_code_assistant.py
pytest tests/test_chat.py
pytest tests/test_vision.py
pytest tests/test_speech.py
```

### Integration Tests

Test full workflow:
```bash
./scripts/06-benchmark.sh --integration
```

### Performance Benchmarks

Standard benchmarks for code models:
- HumanEval
- MBPP
- Aider

Run benchmarks:
```bash
./scripts/06-benchmark.sh --code-benchmark
```

---

## Monitoring and Operations

### Health Checks

All services expose `/health` endpoint for Kubernetes liveness probes.

### Metrics

Prometheus metrics available at:
- vLLM services: `http://<service>:8000/metrics`
- Gateway: `http://gateway:8080/metrics`

### Grafana Dashboards

Import dashboards from `monitoring/grafana-dashboard.json`:
- GPU utilization and temperature
- Memory usage per service
- Request latency and throughput
- Model switching frequency

### Alerts

Alert rules configured in `monitoring/alerts.yaml`:
- GPU temperature > 80°C
- Memory usage > 90%
- Service down > 5 minutes
- Request latency > 10 seconds

---

## User Access Methods

### Web Interface

Open WebUI accessible at `http://<jetson-thor-ip>:3000`

Features:
- Unified chat interface for all services
- File upload for vision tasks
- Voice input/output
- Conversation history

### VS Code Integration

Install Continue extension and configure:
```json
{
  "models": [
    {
      "title": "FamilyAI Code",
      "provider": "openai",
      "model": "qwen2.5-coder-32b",
      "apiBase": "http://<jetson-thor-ip>:8001/v1"
    }
  ]
}
```

### API Access

OpenAI-compatible API:
```bash
curl http://<jetson-thor-ip>:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Mobile Access

Use responsive Web UI or any OpenAI-compatible mobile client.

---

## Security Considerations

### Network Access

- All services run on internal network only by default
- Expose through reverse proxy (Traefik/Nginx) for external access
- Use HTTPS with valid certificates
- Implement rate limiting per user/IP

### Authentication

- Basic auth for Web UI (configure in Open WebUI)
- API token-based auth for programmatic access
- User management in Open WebUI settings

### Data Privacy

- All data processing happens locally on Jetson Thor
- No external API calls
- Conversation history stored locally (optional)
- No telemetry or usage data sent to external servers

---

## Troubleshooting

### Common Issues

**Out of Memory (OOM)**:
- Check `docker stats` or `kubectl top pods`
- Reduce concurrent model loading
- Use model hot-swapping for code assistants
- Increase quantization (FP8 instead of INT4 if needed)

**Slow Inference**:
- Check GPU utilization with `nvidia-smi`
- Verify INT4 quantization is active
- Reduce batch size if needed
- Check for thermal throttling

**Model Download Fails**:
- Verify internet connectivity
- Check HuggingFace Hub status
- Use manual download and mount cache directory

**vLLM Container Crashes**:
- Check CUDA compatibility
- Verify NVIDIA Container Toolkit installation
- Review container logs: `docker logs <container>`

See `docs/05-troubleshooting.md` for detailed guides.

---

## Upgrade Path

### When to Upgrade Models

**Qwen3-Coder Dense Models** (future):
- If Qwen releases Qwen3-Coder-32B/14B/8B dense models
- Expected performance: 10-20% improvement over Qwen2.5-Coder
- Drop-in replacement with same deployment config

**Qwen3-VL**:
- When released, replace Qwen2-VL-7B
- Expected improvements: better vision-language understanding

**Qwen4** (hypothetical):
- Evaluate parameter efficiency gains
- Test on benchmarks before production deployment

### Version Control

- Pin model versions in `vllm/models.yaml`
- Test new models in staging environment first
- Keep previous models as fallback for 2 weeks
- Document performance changes in changelogs

---

## Project Structure Reference

```
FamilyAI/
├── CLAUDE.md                    # This file
├── README.md                    # User-facing documentation
├── docker-compose.yml           # Development deployment
├── .env.example                 # Environment template
├── k3s/                        # Production deployment
├── vllm/                       # Model configurations
├── gateway/                    # Intelligent routing
├── whisper/                    # ASR service
├── piper/                      # TTS service
├── web-ui/                     # Frontend config
├── scripts/                    # Automation scripts
├── monitoring/                 # Observability config
├── tests/                      # Test suites
└── docs/                       # Documentation
```

---

## Support and References

### Official Documentation

- **Qwen Models**: https://qwenlm.github.io/
- **vLLM**: https://docs.vllm.ai/
- **Jetson AI Lab**: https://www.jetson-ai-lab.com/
- **K3s**: https://docs.k3s.io/

### Community Resources

- **jetson-containers**: https://github.com/dusty-nv/jetson-containers
- **Open WebUI**: https://docs.openwebui.com/

### Model Cards

- Qwen2.5-Coder: https://huggingface.co/Qwen/Qwen2.5-Coder-32B-Instruct
- Qwen3-Coder: https://huggingface.co/Qwen/Qwen3-Coder-30B-A3B-Instruct
- Qwen3: https://huggingface.co/Qwen/Qwen3-32B-Instruct
- Qwen2-VL: https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct

---

**Last Updated**: 2025-10-13
**Jetson Thor Platform**: Production Ready
**Primary Models**: Qwen3 Series + Qwen2.5-Coder
