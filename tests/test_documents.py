from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_upload_document():

    login_response = client.post(
        "/login",
        data={
            "username": "pytestuser",
            "password": "testpassword"
        }
    )

    token = login_response.json()["access_token"]

    response = client.post(
        "/upload",
        headers={
            "Authorization": f"Bearer {token}"
        },
        files={
            "file": (
                "test.txt",
                b"Falcon AI is an intelligent business assistant.",
                "text/plain"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "File uploaded and indexed successfully"
    assert data["characters"] > 0