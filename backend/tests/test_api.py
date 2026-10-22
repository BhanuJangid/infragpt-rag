from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert body["docs_indexed"] >= 4
    assert body["llm"] == "mock-offline"


def test_chat_runbook():
    res = client.post("/chat", json={"message": "disk predictive failure on Nutanix"})
    assert res.status_code == 200
    body = res.json()
    assert body["sources"]
    assert any("nutanix" in s["path"] for s in body["sources"])
    assert "Mock" in body["answer"] or "runbook" in body["answer"].lower() or "disk" in body["answer"].lower()


def test_chat_lists_vms():
    res = client.post("/chat", json={"message": "list powered off VMs"})
    assert res.status_code == 200
    body = res.json()
    names = [c["name"] for c in body["tool_calls"]]
    assert "list_vms" in names
    assert "batch-etl-01" in body["answer"]
