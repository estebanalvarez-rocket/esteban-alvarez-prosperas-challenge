from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.core.database import get_db
from app.main import app


def test_register_flow(test_client, monkeypatch):
    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(
        "app.api.routes.auth.create_user",
        lambda db, payload: SimpleNamespace(
            id=uuid4(),
            email=payload.email.lower(),
            created_at=datetime.now(UTC),
        ),
    )

    response = test_client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword123"},
    )

    assert response.status_code in [201, 409]
    app.dependency_overrides = {}
