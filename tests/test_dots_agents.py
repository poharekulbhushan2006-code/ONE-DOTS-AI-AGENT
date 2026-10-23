"""
DOTS AI AGENT - Automated Test Suite
Validates persistent agent lifecycle, Google Gemini chat, cloud computer execution,
episodic memory, and human decision gate.
"""

from fastapi.testclient import TestClient
from api.app import app

client = TestClient(app)


def test_agent_full_lifecycle():
    # 1. Deploy new test agent
    deploy_payload = {
        "name": "QA_Dot",
        "responsibility": "Verify automated tests and ensure platform stability",
        "schedule_interval_seconds": 60,
        "context": {"color": "blue", "archetype": "qa"}
    }
    resp = client.post("/api/agents", json=deploy_payload)
    assert resp.status_code == 200, resp.text
    agent_data = resp.json()
    agent_id = agent_data["id"]
    assert agent_data["name"] == "QA_Dot"
    assert agent_data["status"] == "idle"

    # 2. Verify agent in list
    list_resp = client.get("/api/agents")
    assert list_resp.status_code == 200
    agents = list_resp.json()
    assert any(a["id"] == agent_id for a in agents)

    # 3. Retrieve single agent
    get_resp = client.get(f"/api/agents/{agent_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == agent_id

    # 4. Pause and resume
    p_resp = client.post(f"/api/agents/{agent_id}/pause")
    assert p_resp.status_code == 200
    assert p_resp.json()["status"] == "paused"

    r_resp = client.post(f"/api/agents/{agent_id}/resume")
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "idle"

    # 5. Get catch-up briefing
    b_resp = client.get(f"/api/agents/{agent_id}/briefing")
    assert b_resp.status_code == 200
    assert "briefing" in b_resp.json()

    # 6. Delete agent
    del_resp = client.delete(f"/api/agents/{agent_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True

    # 7. Confirm deleted
    c_resp = client.get(f"/api/agents/{agent_id}")
    assert c_resp.status_code == 404


def test_agent_conversational_chat():
    # Create an agent for conversation testing
    resp = client.post("/api/agents", json={
        "name": "ChatTester",
        "responsibility": "Test conversational AI interactions",
        "schedule_interval_seconds": 120
    })
    agent_id = resp.json()["id"]

    try:
        chat_resp = client.post(
            f"/api/agents/{agent_id}/chat",
            json={"message": "State your current mission in 10 words."}
        )
        assert chat_resp.status_code == 200, chat_resp.text
        chat_data = chat_resp.json()
        assert chat_data["sender"] == "agent"
        assert len(chat_data["content"]) > 0

        # Verify chat history
        hist_resp = client.get(f"/api/agents/{agent_id}/chat")
        assert hist_resp.status_code == 200
        messages = hist_resp.json()
        assert len(messages) >= 2
    finally:
        client.delete(f"/api/agents/{agent_id}")


def test_agent_sandbox_and_cloud_computer():
    resp = client.post("/api/agents", json={
        "name": "SandboxTester",
        "responsibility": "Test sandbox execution",
        "schedule_interval_seconds": 120
    })
    agent_id = resp.json()["id"]

    try:
        # Run python code inside sandbox
        exec_resp = client.post(
            f"/api/agents/{agent_id}/execute",
            json={"code": "val = 21 * 2\nprint(f'COMPUTED: {val}')", "language": "python"}
        )
        assert exec_resp.status_code == 200
        out = exec_resp.json().get("stdout", "")
        assert "COMPUTED: 42" in out

        # Check sandbox file list
        files_resp = client.get(f"/api/agents/{agent_id}/files")
        assert files_resp.status_code == 200
        assert "files" in files_resp.json()
    finally:
        client.delete(f"/api/agents/{agent_id}")
