# Control Plane Overview

The control plane service (port 9000) manages model metadata, download jobs, and dynamic routing hints.

## Endpoints

- `GET /health` – readiness probe.
- `GET /models` – catalog with provider, latency, cost, and endpoint metadata.
- `POST /models/{id}/download` – queue a download; creates a `.pending` marker under `control-plane/downloads/`.
- `GET /profiles` – list available routing profiles and the active profile.
- `POST /profiles/{name}/activate` – switch the active profile.
- `POST /profiles/{name}/routing` – mutate routing tables inside `models.yaml` (persists to the mounted ConfigMap).
- `POST /recommend` – OpenRouter-style selection; accepts `task`, `context_tokens`, `priority` (`balanced`, `speed`, `quality`, `cost`), and `allow_cloud`.

## Recommendation Heuristics

1. Rejects models without sufficient context window.
2. Applies priority weighting:
   - `speed`: lowest latency wins.
   - `quality`: favors higher VRAM footprints.
   - `cost`: minimizes `cost_per_million`.
   - `balanced`: combines latency, memory, and cost.
3. Penalizes cloud providers unless `allow_cloud` is `true`.
4. Returns metadata, score, and rationale to the gateway.

## Admin UI Stub

`admin-ui` serves a static dashboard pointing operators at the control plane API. Replace the stub with a richer SPA once design assets are ready. Build commands are thin wrappers around `build.js` to avoid large JS dependencies on the Jetson host.

## Operational Notes

- Update `control-plane/config/models.yaml` when introducing new models or third-party endpoints.
- The ConfigMap in `k3s/control-plane-deployment.yaml` mirrors the same file; re-apply the manifest after edits.
- For automated downloads, extend `scripts/02-pull-models.sh` or add a sidecar job that consumes `.pending` markers.
- Audit `metadata.source` in `gateway` responses to confirm whether selections came from the control plane (dynamic) or static fallbacks.
