from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_register_user():

    response = client.post(
        "/register",
        json={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    assert response.status_code == 200


def test_login_user():

    response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_profile():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/profile",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "Welcome" in data["message"]