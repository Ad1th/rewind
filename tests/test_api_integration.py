import pytest
from fastapi.testclient import TestClient

from backend.main import app
from agent.runtime.contracts import Action, RiskAssessment
from agent.tools.models import ReversibilityClass, RiskLevel


@pytest.fixture
def client():
    return TestClient(app)


def test_workspace_and_session_api(client: TestClient):
    # 1. Create workspace
    resp = client.post("/api/v1/workspaces", json={"workspace_root": "/tmp/test_ws", "name": "API Workspace"})
    assert resp.status_code == 201
    ws_data = resp.json()
    assert ws_data["workspace_root"] == "/tmp/test_ws"
    ws_id = ws_data["workspace_id"]

    # Get workspace
    resp = client.get(f"/api/v1/workspaces/{ws_id}")
    assert resp.status_code == 200
    assert resp.json()["workspace_id"] == ws_id

    # 2. Create session
    resp = client.post("/api/v1/sessions", json={"workspace_root": "/tmp/test_ws", "goal_prompt": "Refactor router"})
    assert resp.status_code == 201
    sess_data = resp.json()
    sess_id = sess_data["session_id"]
    assert sess_data["status"] == "SESSION_CREATED"

    # Pause session
    resp = client.post(f"/api/v1/sessions/{sess_id}/pause")
    assert resp.status_code == 200
    assert resp.json()["status"] == "PAUSED"

    # Resume session
    resp = client.post(f"/api/v1/sessions/{sess_id}/resume")
    assert resp.status_code == 200
    assert resp.json()["status"] == "RUNNING"


def test_rollback_trigger_api(client: TestClient, tmp_path):
    ws_path = str(tmp_path / "workspace")
    tmp_path.mkdir(exist_ok=True)

    # Trigger rollback via API
    resp = client.post(
        "/api/v1/rollbacks",
        json={
            "session_id": "sess-api-rollback",
            "target_step_index": 1,
            "workspace_root": ws_path,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["rollback_id"] is not None
    assert data["session_id"] == "sess-api-rollback"
    assert data["status"] in ("RESTORED", "SKIPPED_ALREADY_AT_TARGET")


def test_websocket_telemetry_stream(client: TestClient):
    session_id = "sess-ws-stream"
    with client.websocket_connect(f"/api/v1/sessions/{session_id}/stream") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert "pong" in data
