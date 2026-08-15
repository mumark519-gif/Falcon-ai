from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token():
    response = client.post("/login", data={"username": "pytestuser", "password": "testpassword"})
    return response.json()["access_token"]


def test_commercial_plans():
    response = client.get("/commercial/plans")
    assert response.status_code == 200
    assert "free" in response.json()["plans"]


def test_personal_workspace_and_usage():
    token = _token()
    headers = {"Authorization": f"Bearer {token}"}
    organization = client.get("/commercial/organization", headers=headers)
    assert organization.status_code == 200
    data = organization.json()
    assert data["plan"] == "free"
    usage = client.get("/commercial/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["limit"] >= usage.json()["used"]


def test_api_key_lifecycle():
    token = _token()
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/commercial/api-keys", headers=headers, json={"name": "pytest"})
    assert created.status_code == 200
    body = created.json()
    assert body["api_key"].startswith("falcon_")
    listed = client.get("/commercial/api-keys", headers=headers)
    assert listed.status_code == 200
    assert any(row["id"] == body["id"] for row in listed.json())
    revoked = client.delete(f"/commercial/api-keys/{body['id']}", headers=headers)
    assert revoked.status_code == 200
