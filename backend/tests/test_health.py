from app.main import app


def test_health_returns_dependency_report(test_client, monkeypatch):
    monkeypatch.setattr(
        "app.main.get_health_report",
        lambda: {
            "status": "ok",
            "service": "Reports Platform",
            "version": "0.1.0",
            "environment": "test",
            "dependencies": {
                "database": {"status": "ok", "detail": "reachable"},
                "sqs": {"status": "ok", "detail": "reachable"},
                "s3": {"status": "ok", "detail": "reachable"},
                "cloudwatch": {"status": "ok", "detail": "reachable"},
            },
        },
    )

    response = test_client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "Reports Platform"
    assert body["dependencies"]["database"]["status"] == "ok"
    assert body["dependencies"]["sqs"]["status"] == "ok"
    assert body["dependencies"]["s3"]["status"] == "ok"
    assert body["dependencies"]["cloudwatch"]["status"] == "ok"

    app.dependency_overrides = {}
