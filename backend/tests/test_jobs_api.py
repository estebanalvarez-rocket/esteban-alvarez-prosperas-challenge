from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.tables import JobPriority, JobStatus
from app.services import job_service


def test_post_jobs_accepts_job_and_returns_priority(test_client, fake_user, monkeypatch):
    job_id = uuid4()

    def fake_create_job(db, current_user, payload):
        assert current_user.email == fake_user.email
        assert payload.report_type == "sales_summary"
        return SimpleNamespace(
            job_id=job_id,
            user_id=UUID(str(fake_user.id)),
            status=JobStatus.PENDING,
            priority=JobPriority.STANDARD,
            report_type=payload.report_type,
            report_format=payload.format,
            date_from=payload.date_from,
            date_to=payload.date_to,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            result_url=None,
            error_message=None,
            attempt_count=0,
            next_retry_at=None,
        )

    def override_db():
        yield object()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    monkeypatch.setattr("app.api.routes.jobs.create_job", fake_create_job)

    response = test_client.post(
        "/api/jobs",
        json={
            "report_type": "sales_summary",
            "date_from": str(date(2026, 3, 1)),
            "date_to": str(date(2026, 3, 21)),
            "format": "json",
        },
    )

    assert response.status_code == 201
    assert response.json() == {"job_id": str(job_id), "status": "PENDING", "priority": "STANDARD"}

    app.dependency_overrides = {}


def test_get_job_priority_routes_high_priority_reports():
    assert job_service.get_job_priority("fraud_alert") == JobPriority.HIGH
    assert job_service.get_job_priority("sales_summary") == JobPriority.STANDARD
