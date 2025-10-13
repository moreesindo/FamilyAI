from __future__ import annotations

import asyncio
import logging
import os
from functools import lru_cache
from typing import Any, Dict, Literal, Optional

import httpx
import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())

TaskKind = Literal["code", "chat", "vision", "asr", "tts"]
CONTROL_PLANE_URL = os.getenv("CONTROL_PLANE_URL")


class RouteRequest(BaseModel):
    task: TaskKind
    context_tokens: Optional[int] = Field(None, ge=0)
    complexity: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Rough complexity score (0=trivial, 1=advanced).",
    )
    priority: Optional[Literal["speed", "quality", "cost", "balanced"]] = None
    payload: Optional[Dict[str, Any]] = None


class RouteResponse(BaseModel):
    model: str
    endpoint: str
    metadata: Dict[str, Any]


class ProxyRequest(BaseModel):
    task: TaskKind
    payload: Dict[str, Any]
    context_tokens: Optional[int] = None
    complexity: Optional[float] = None
    priority: Optional[Literal["speed", "quality", "cost", "balanced"]] = None


def load_routing_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not data:
        raise RuntimeError("Routing configuration is empty")
    return data


@lru_cache(maxsize=1)
def get_config() -> Dict[str, Any]:
    config_path = os.getenv("ROUTING_CONFIG", "/app/config/routing.yaml")
    logger.info("Loading routing configuration from %s", config_path)
    return load_routing_config(config_path)


def select_code_model(config: Dict[str, Any], request: RouteRequest) -> str:
    thresholds = config["policies"]["code"].get("thresholds", {})
    long_context_limit = thresholds.get("context_tokens", 8_000)
    if request.context_tokens and request.context_tokens > long_context_limit:
        return config["policies"]["code"]["long_context"]
    if request.priority == "speed":
        # fallback to MoE model for faster streaming
        return config["policies"]["code"].get("long_context")
    return config["policies"]["code"]["default"]


def select_chat_model(config: Dict[str, Any], request: RouteRequest) -> str:
    thresholds = config["policies"]["chat"].get("thresholds", {})
    complexity = request.complexity or 0.3
    if request.priority == "speed" and "lightweight" in config["policies"]["chat"]:
        return config["policies"]["chat"]["lightweight"]
    complexity_cutoff = thresholds.get("complexity", 0.6)
    if complexity >= complexity_cutoff:
        return config["policies"]["chat"].get("complex")
    return config["policies"]["chat"].get("balanced")


SELECTORS = {
    "code": select_code_model,
    "chat": select_chat_model,
}

app = FastAPI(title="FamilyAI Intelligent Gateway", version="0.1.0")


@app.get("/health", tags=["health"])
async def health() -> Dict[str, str]:
    status: Dict[str, str] = {"status": "ok"}
    if CONTROL_PLANE_URL:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{CONTROL_PLANE_URL.rstrip('/')}/health")
                response.raise_for_status()
                status["control_plane"] = response.json().get("status", "ok")
        except Exception:
            status["control_plane"] = "degraded"
    return status


async def recommend_via_control_plane(policy: Dict[str, Any], request: RouteRequest) -> Optional[RouteResponse]:
    if not CONTROL_PLANE_URL or not policy.get("control_plane_profile"):
        return None

    payload = {
        "task": request.task,
        "context_tokens": request.context_tokens or 0,
        "priority": request.priority or "balanced",
        "allow_cloud": bool(policy.get("allow_cloud", False)),
    }
    url = f"{CONTROL_PLANE_URL.rstrip('/')}/recommend"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("Control plane recommendation failed: %s", exc)
        return None

    data = response.json()
    model_info = data.get("model") or {}
    model_id = model_info.get("id")
    if not model_id:
        logger.warning("Control plane response missing model id: %s", data)
        return None
    endpoint = model_info.get("endpoint")
    config = get_config()
    if not endpoint:
        endpoint = config["models"].get(model_id, {}).get("endpoint")
    if not endpoint:
        logger.warning("Unable to resolve endpoint for model %s", model_id)
        return None

    metadata = dict(model_info)
    metadata["score"] = data.get("score")
    metadata["rationale"] = data.get("rationale", [])
    metadata["source"] = "control-plane"
    return RouteResponse(model=model_id, endpoint=endpoint, metadata=metadata)


async def resolve_route(request: RouteRequest) -> RouteResponse:
    config = get_config()
    policy = config["policies"].get(request.task)
    if not policy:
        raise HTTPException(status_code=404, detail=f"Unsupported task: {request.task}")

    dynamic_route = await recommend_via_control_plane(policy, request)
    if dynamic_route:
        return dynamic_route

    selector = SELECTORS.get(request.task, lambda _, __: policy.get("default"))
    model_id = selector(config, request)

    model_cfg = config["models"].get(model_id)
    if not model_cfg:
        raise HTTPException(status_code=500, detail=f"Unknown model id {model_id}")

    metadata = dict(model_cfg)
    metadata["source"] = "static"
    return RouteResponse(model=model_id, endpoint=model_cfg["endpoint"], metadata=metadata)


async def proxy_request(client: httpx.AsyncClient, endpoint: str, payload: Dict[str, Any]) -> httpx.Response:
    try:
        response = await client.post(endpoint, json=payload, timeout=120)
        response.raise_for_status()
        return response
    except httpx.RequestError as exc:  # pragma: no cover - network failure path
        logger.error("Gateway failed to reach %s: %s", endpoint, exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/v1/route", response_model=RouteResponse, tags=["routing"])
async def route(request: RouteRequest) -> RouteResponse:
    return await resolve_route(request)


@app.post("/v1/proxy", tags=["proxy"])
async def proxy(proxy_request_body: ProxyRequest) -> Dict[str, Any]:
    routing = await resolve_route(RouteRequest(**proxy_request_body.model_dump()))
    async with httpx.AsyncClient() as client:
        response = await proxy_request(client, routing.endpoint, proxy_request_body.payload)
    return {
        "model": routing.model,
        "endpoint": routing.endpoint,
        "response": response.json(),
    }


@app.on_event("startup")
async def warmup() -> None:
    # Warm up cache and verify config structure
    config = get_config()
    required_sections = {"models", "policies"}
    if not required_sections.issubset(config):
        raise RuntimeError("Routing configuration missing required sections")
    # Optionally ping dependent services in the background
    async with httpx.AsyncClient(timeout=5.0) as client:
        tasks = []
        for model in config["models"].values():
            health_endpoint = model.get("health")
            if health_endpoint:
                tasks.append(client.get(health_endpoint))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
