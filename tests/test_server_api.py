import pytest
from fastapi.testclient import TestClient

def test_unauthenticated_api_rejected(unauth_client):
    """Verifies that all API endpoints strictly reject unauthenticated requests."""
    assert unauth_client.get("/api/status").status_code == 403
    assert unauth_client.get("/api/projects").status_code == 403
    assert unauth_client.get("/api/sessions").status_code == 403
    assert unauth_client.get("/api/tasks").status_code == 403
    assert unauth_client.get("/api/settings").status_code == 403
    assert unauth_client.get("/api/models").status_code == 403


def test_status_endpoint(client):
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert "active_project" in data
    assert "confirm_mode" in data


def test_projects_endpoints(client, tmp_path):
    proj_dir = tmp_path / "test_api_proj"
    proj_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create project
    create_resp = client.post("/api/projects", json={
        "name": "API Test Project",
        "path": str(proj_dir),
        "make_active": True
    })
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["name"] == "API Test Project"

    # 2. List projects
    list_resp = client.get("/api/projects")
    assert list_resp.status_code == 200
    projs = list_resp.json()
    assert any(p["id"] == created["id"] for p in projs)

    # 3. Activate project
    act_resp = client.post(f"/api/projects/{created['id']}/activate")
    assert act_resp.status_code == 200
    assert act_resp.json()["success"] is True

    # 4. Project files listing
    (proj_dir / "sample.txt").write_text("hello", encoding="utf-8")
    files_resp = client.get(f"/api/projects/{created['id']}/files")
    assert files_resp.status_code == 200
    file_items = files_resp.json()["items"]
    assert any(f["name"] == "sample.txt" for f in file_items)

    # 5. File content preview
    content_resp = client.get(f"/api/projects/{created['id']}/file_content?file_path=sample.txt")
    assert content_resp.status_code == 200
    assert content_resp.json()["content"] == "hello"

    # 6. Path traversal security protection
    traversal_resp = client.get(f"/api/projects/{created['id']}/files?subdir=../../")
    assert traversal_resp.status_code in (400, 403, 404)

    # 7. Delete project
    del_resp = client.delete(f"/api/projects/{created['id']}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


def test_sessions_endpoints(client):
    # 1. List sessions
    list_resp = client.get("/api/sessions")
    assert list_resp.status_code == 200
    sessions = list_resp.json()
    assert isinstance(sessions, list)

    # 2. Create session
    create_resp = client.post("/api/sessions", json={
        "title": "API Session 1",
        "make_active": True
    })
    assert create_resp.status_code == 200
    created = create_resp.json()
    assert created["title"] == "API Session 1"

    # 3. Activate session
    act_resp = client.post(f"/api/sessions/{created['id']}/activate")
    assert act_resp.status_code == 200
    assert act_resp.json()["success"] is True

    # 4. Delete session
    del_resp = client.delete(f"/api/sessions/{created['id']}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


def test_tasks_endpoints(client):
    # 1. Create scheduled task
    create_resp = client.post("/api/tasks", json={
        "title": "API Task 1",
        "cron_expression": "10 8 * * *",
        "prompt": "Check git repository status"
    })
    assert create_resp.status_code == 200
    task = create_resp.json()
    assert task["title"] == "API Task 1"
    assert task["id"] > 0

    # 2. List tasks
    list_resp = client.get("/api/tasks")
    assert list_resp.status_code == 200
    tasks = list_resp.json()
    assert any(t["id"] == task["id"] for t in tasks)

    # 3. Toggle task
    toggle_resp = client.post(f"/api/tasks/{task['id']}/toggle", json={"is_active": False})
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["is_active"] is False

    # 4. Delete task
    del_resp = client.delete(f"/api/tasks/{task['id']}")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True


def test_settings_endpoints(client):
    # 1. Get settings
    get_resp = client.get("/api/settings")
    assert get_resp.status_code == 200
    settings_data = get_resp.json()
    assert "confirm_mode" in settings_data
    assert "language" in settings_data

    # 2. Update setting
    post_resp = client.post("/api/settings", json={"key": "language", "value": "en"})
    assert post_resp.status_code == 200
    assert post_resp.json()["value"] == "en"

    # Verify updated
    get_resp_after = client.get("/api/settings")
    assert get_resp_after.json()["language"] == "en"


def test_models_endpoints(client):
    # 1. Get models
    models_resp = client.get("/api/models")
    assert models_resp.status_code == 200
    models_data = models_resp.json()
    assert "models" in models_data
    assert len(models_data["models"]) >= 5

    # 2. Create custom model
    create_resp = client.post("/api/models", json={
        "id": "custom-test-model",
        "name": "Custom Test Model",
        "description": "Test model"
    })
    assert create_resp.status_code == 200
    assert create_resp.json()["success"] is True

    # 3. Delete custom model
    del_resp = client.delete("/api/models/custom-test-model")
    assert del_resp.status_code == 200
    assert del_resp.json()["success"] is True



def test_static_files_hosting(client):
    """Verifies that static assets or root page are served cleanly."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Gravigram" in resp.text or "Antigravity" in resp.text or "flutter" in resp.text
