from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field

BASE_PATH = Path(os.getenv("CONTROL_PLANE_ROOT", Path(__file__).resolve().parent.parent))
CONFIG_PATH = BASE_PATH / "config" / "models.yaml"
STATE_PATH = BASE_PATH / "config" / "state.json"

def _load_yaml(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_state() -> Dict[str, object]:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"active_profile": "default"}


def _write_state(state: Dict[str, object]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


@lru_cache(maxsize=1)
def get_config() -> Dict[str, object]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Model config missing at {CONFIG_PATH}")
    return _load_yaml(CONFIG_PATH)


app = FastAPI(title="FamilyAI Control Plane", version="0.2.0")


class ModelDescriptor(BaseModel):
    id: str
    provider: str
    service: Optional[str] = None
    label: str
    task: str
    context: Optional[int] = None
    latency_ms: Optional[int] = None
    cost_per_million: Optional[float] = None
    memory_gb: Optional[float] = None
    endpoint: Optional[str] = None
    auth_env: Optional[str] = None


class ProfileDescriptor(BaseModel):
    name: str
    routing: Dict[str, str]
    description: Optional[str] = None


class ProfilesResponse(BaseModel):
    active_profile: str
    profiles: List[ProfileDescriptor]


class RecommendationRequest(BaseModel):
    task: str
    context_tokens: int = Field(4096, ge=0)
    priority: str = Field("balanced", description="balanced | speed | quality | cost")
    allow_cloud: bool = True


class RecommendationResponse(BaseModel):
    model: ModelDescriptor
    score: float
    rationale: List[str]


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/models", response_model=List[ModelDescriptor])
def list_models() -> List[ModelDescriptor]:
    config = get_config()
    models = []
    for key, value in config.get("models", {}).items():
        entry = ModelDescriptor(id=key, **value)
        models.append(entry)
    return models


@app.get("/profiles", response_model=ProfilesResponse)
def list_profiles() -> ProfilesResponse:
    config = get_config()
    profiles: List[ProfileDescriptor] = []
    for name, data in config.get("profiles", {}).items():
        profiles.append(ProfileDescriptor(name=name, routing=data.get("routing", {}), description=data.get("description")))
    state = _load_state()
    return ProfilesResponse(active_profile=state.get("active_profile", "default"), profiles=profiles)


@app.post("/profiles/{profile_name}/activate")
def activate_profile(profile_name: str) -> Dict[str, str]:
    config = get_config()
    if profile_name not in config.get("profiles", {}):
        raise HTTPException(status_code=404, detail=f"Unknown profile {profile_name}")
    state = _load_state()
    state["active_profile"] = profile_name
    _write_state(state)
    return {"status": "ok", "active_profile": profile_name}


def _score_model(model: ModelDescriptor, request: RecommendationRequest) -> tuple[float, list[str]]:
    score = 0.0
    rationale: List[str] = []

    # Context fit
    if model.context and model.context < request.context_tokens:
        rationale.append("Insufficient context window")
        return -1e9, rationale

    if request.priority == "speed":
        latency = model.latency_ms or 10_000
        score -= latency / 1000
        rationale.append(f"Speed priority latency={latency}ms")
    elif request.priority == "cost":
        cost = model.cost_per_million or 0.0
        score -= cost
        rationale.append(f"Cost priority cost={cost}")
    elif request.priority == "quality":
        # treat bigger memory footprint as proxy for quality
        quality = model.memory_gb or 1
        score += quality
        rationale.append(f"Quality priority memory={quality}GB")
    else:  # balanced
        latency = model.latency_ms or 10_000
        cost = model.cost_per_million or 0.0
        score += (model.memory_gb or 1) * 0.6
        score -= latency / 1500
        score -= cost * 0.2
        rationale.append(f"Balanced score latency={latency} cost={cost}")

    # Provider preference: local before cloud unless allowed
    if model.provider.startswith("cloud"):
        if not request.allow_cloud:
            rationale.append("Cloud models disabled")
            return -1e9, rationale
        score -= 0.5  # bias toward local
        rationale.append("Cloud penalty -0.5")
    else:
        score += 0.2
        rationale.append("Local bonus +0.2")
    return score, rationale


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest = Body(...)) -> RecommendationResponse:
    config = get_config()
    models = [ModelDescriptor(id=key, **value) for key, value in config.get("models", {}).items() if value.get("task") == request.task]
    if not models:
        raise HTTPException(status_code=404, detail=f"No models available for task {request.task}")

    best_score = -1e9
    best_model = None
    best_rationale: List[str] = []

    for model in models:
        score, rationale = _score_model(model, request)
        if score > best_score:
            best_score = score
            best_model = model
            best_rationale = rationale

    if best_model is None:
        raise HTTPException(status_code=503, detail="No suitable model found")

    return RecommendationResponse(model=best_model, score=best_score, rationale=best_rationale)


class DownloadRequest(BaseModel):
    model_id: str


@app.post("/models/{model_id}/download")
def schedule_download(model_id: str, body: DownloadRequest) -> Dict[str, str]:
    if model_id != body.model_id:
        raise HTTPException(status_code=400, detail="Model id mismatch")
    config = get_config()
    if model_id not in config.get("models", {}):
        raise HTTPException(status_code=404, detail="Unknown model")
    download_dir = Path(os.getenv("MODEL_DOWNLOAD_DIR", BASE_PATH / "downloads"))
    download_dir.mkdir(parents=True, exist_ok=True)
    (download_dir / f"{model_id}.pending").touch()
    return {"status": "scheduled", "model_id": model_id}


class UpdateRoutingRequest(BaseModel):
    task: str
    model_id: str


@app.post("/profiles/{profile_name}/routing")
def update_routing(profile_name: str, request: UpdateRoutingRequest) -> Dict[str, object]:
    config = get_config()
    profiles = config.setdefault("profiles", {})
    if profile_name not in profiles:
        raise HTTPException(status_code=404, detail=f"Unknown profile {profile_name}")
    if request.model_id not in config.get("models", {}):
        raise HTTPException(status_code=404, detail=f"Unknown model {request.model_id}")
    profiles[profile_name].setdefault("routing", {})[request.task] = request.model_id
    CONFIG_PATH.write_text(yaml.safe_dump(config, sort_keys=True), encoding="utf-8")
    get_config.cache_clear()
    return {"status": "ok", "profile": profile_name, "routing": profiles[profile_name]["routing"]}
