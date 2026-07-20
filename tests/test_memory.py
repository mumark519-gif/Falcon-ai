from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_memories():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/memories",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

def test_save_memory():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/memory",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "key": "favorite_color",
            "value": "blue"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Memory saved successfully"

def test_update_memory():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/memory",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "key": "favorite_color",
            "value": "red"
        }
    )

    assert response.status_code == 200

    memories_response = client.get(
        "/memories",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    memories = memories_response.json()

    favorite_memory = next(
        memory
        for memory in memories
        if memory["key"] == "favorite_color"
    )

    assert favorite_memory["value"] == "red"