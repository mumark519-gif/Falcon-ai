from fastapi.testclient import TestClient

from unittest.mock import patch

from app.main import app


client = TestClient(app)


def test_create_chat():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/create_chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Test Chat"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "chat_id" in data
    assert data["title"] == "Test Chat"

def test_get_chats():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(
        "/chats",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

def test_get_chat_messages():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    create_response = client.post(
        "/create_chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Message Test Chat"
        }
    )

    chat_id = create_response.json()["chat_id"]

    response = client.get(
        f"/chat/{chat_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

def test_rename_chat():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    create_response = client.post(
        "/create_chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Old Title"
        }
    )

    chat_id = create_response.json()["chat_id"]

    response = client.put(
        "/rename-chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "chat_id": chat_id,
            "title": "New Title"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Chat renamed successfully"
    assert data["chat"]["title"] == "New Title"

def test_delete_chat():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    create_response = client.post(
        "/create_chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Chat To Delete"
        }
    )

    chat_id = create_response.json()["chat_id"]

    response = client.delete(
        f"/chat/{chat_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Chat deleted successfully"

@patch(
    "app.services.chat_service.ask_ai",
    return_value="Mocked Falcon AI response"
)
@patch(
    "app.services.chat_service.extract_memory",
    return_value={
        "favorite_color": "green"
    }
)
@patch(
    "app.services.chat_service.generate_chat_title",
    return_value="Test Chat"
)
def test_chat_with_mocked_ai(
    mock_title,
    mock_memory,
    mock_ai
):

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    create_response = client.post(
        "/create_chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "New Chat"
        }
    )

    chat_id = create_response.json()["chat_id"]

    response = client.post(
        "/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "chat_id": chat_id,
            "message": "My favorite color is green"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["response"] == "Mocked Falcon AI response"

    mock_ai.assert_called_once()
    mock_memory.assert_called_once()