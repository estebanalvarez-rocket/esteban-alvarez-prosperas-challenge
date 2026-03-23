from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from app.core.auth import encode_token
from app.models.schemas import JobRead, JobRealtimeMessage
from app.models.tables import JobPriority, JobStatus


def test_jobs_websocket_streams_snapshot(test_client, fake_user, monkeypatch):
    job_id = uuid4()

    monkeypatch.setattr(
        "app.api.routes.realtime.build_jobs_payload",
        lambda user_id: JobRealtimeMessage(
            type="jobs.snapshot",
            jobs=[
                JobRead(
                    job_id=job_id,
                    user_id=UUID(str(fake_user.id)),
                    status=JobStatus.PENDING,
                    priority=JobPriority.HIGH,
                    report_type="fraud_alert",
                    report_format="json",
                    date_from=date(2026, 3, 1),
                    date_to=date(2026, 3, 2),
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC),
                    result_url=None,
                    error_message=None,
                    attempt_count=0,
                    next_retry_at=None,
                )
            ],
        ),
    )
    monkeypatch.setattr("app.api.routes.realtime.resolve_user", lambda token: fake_user)

    token = encode_token({"sub": str(fake_user.id), "email": fake_user.email})
    with test_client.websocket_connect(f"/api/ws/jobs?token={token}") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "jobs.snapshot"
    assert payload["jobs"][0]["priority"] == "HIGH"
