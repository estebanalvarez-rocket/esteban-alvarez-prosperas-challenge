from fastapi.testclient import TestClient

from app.main import app


def test_register_flow():
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/register",
            json={"email": "newuser@example.com", "password": "securepassword123"},
        )

    assert response.status_code in [201, 409]
