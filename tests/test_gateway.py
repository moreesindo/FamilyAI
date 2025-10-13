import os
from importlib import reload

import pytest
from fastapi.testclient import TestClient

from gateway.app import main


@pytest.fixture(autouse=True)
def set_config(tmp_path):
    config_path = os.path.join(os.path.dirname(__file__), "fixtures", "routing_policy.yaml")
    os.environ["ROUTING_CONFIG"] = config_path
    main.get_config.cache_clear()
    globals()["main"] = reload(main)
    yield
    main.get_config.cache_clear()


def test_route_chat_balanced():
    client = TestClient(main.app)
    response = client.post("/v1/route", json={"task": "chat", "complexity": 0.3})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "fast"


def test_route_chat_complex():
    client = TestClient(main.app)
    response = client.post("/v1/route", json={"task": "chat", "complexity": 0.9})
    assert response.status_code == 200
    assert response.json()["model"] == "accurate"


def test_route_unknown_task():
    client = TestClient(main.app)
    response = client.post("/v1/route", json={"task": "tts"})
    assert response.status_code == 404


def test_health_endpoint():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] in {"ok", "degraded"}
