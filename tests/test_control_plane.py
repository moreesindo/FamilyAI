import importlib.util
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "control-plane" / "app" / "main.py"
spec = importlib.util.spec_from_file_location("control_plane_main", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
sys.modules["control_plane_main"] = module
assert spec.loader is not None
spec.loader.exec_module(module)  # type: ignore

client = TestClient(module.app)  # type: ignore


def setup_function(_function):
    # reset state file before each test
    state_path = ROOT / "control-plane" / "config" / "state.json"
    if state_path.exists():
        state_path.unlink()
    module.get_config.cache_clear()  # type: ignore


def test_list_models_contains_ids():
    response = client.get("/models")
    assert response.status_code == 200
    payload = response.json()
    assert any(model["id"].endswith("local") for model in payload)


def test_recommend_balanced_prefers_local_when_allowed():
    body = {"task": "chat", "context_tokens": 1024, "priority": "balanced", "allow_cloud": True}
    response = client.post("/recommend", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["model"]["provider"] == "local"
    assert data["model"]["id"].endswith("local")


def test_recommend_disallows_cloud_when_disabled():
    body = {"task": "chat", "context_tokens": 1024, "priority": "speed", "allow_cloud": False}
    response = client.post("/recommend", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["model"]["provider"] == "local"


def test_activate_profile_updates_state():
    response = client.post("/profiles/default/activate")
    assert response.status_code == 200
    payload = response.json()
    assert payload["active_profile"] == "default"
    # state file should reflect change
    state_path = Path(__file__).resolve().parents[1] / "control-plane" / "config" / "state.json"
    assert json.loads(state_path.read_text())["active_profile"] == "default"
