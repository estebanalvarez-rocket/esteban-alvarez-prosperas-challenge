import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

from app.models.tables import JobPriority
from app.services import report_simulation_service
from app.worker import runner


class FakeDb:
    def close(self):
        return None


class FakeSqs:
    def __init__(self):
        self.deleted = []
        self.visibility_changes = []

    def delete_message(self, **kwargs):
        self.deleted.append(kwargs)

    def change_message_visibility(self, **kwargs):
        self.visibility_changes.append(kwargs)


class FakeS3:
    def __init__(self):
        self.objects = []

    def put_object(self, **kwargs):
        self.objects.append(kwargs)


def build_message(job_id, report_type="sales_summary", receive_count=1):
    return {
        "Body": json.dumps(
            {
                "job_id": str(job_id),
                "user_id": str(uuid4()),
                "report_type": report_type,
                "priority": "STANDARD",
            }
        ),
        "ReceiptHandle": "receipt-1",
        "Attributes": {"ApproximateReceiveCount": str(receive_count)},
    }


def test_process_message_marks_completed_and_deletes_message(monkeypatch):
    fake_db = FakeDb()
    fake_sqs = FakeSqs()
    fake_s3 = FakeS3()
    job_id = uuid4()

    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(
        runner,
        "claim_job",
        lambda db, incoming_job_id: SimpleNamespace(job_id=incoming_job_id, priority=JobPriority.STANDARD),
    )
    monkeypatch.setattr(
        runner,
        "mark_job_completed",
        lambda db, incoming_job_id, result_url: setattr(fake_db, "completed", (incoming_job_id, result_url)),
    )
    monkeypatch.setattr(
        runner,
        "generate_result",
        lambda incoming_job_id, report_type, receive_count: (f"reports/{incoming_job_id}.json", b"{}"),
    )
    monkeypatch.setattr(
        runner,
        "get_boto3_client",
        lambda service_name: fake_sqs if service_name == "sqs" else fake_s3,
    )

    runner.process_message(runner.settings.sqs_standard_queue_url, build_message(job_id), runner.WorkerState())

    assert fake_s3.objects
    assert fake_sqs.deleted == [{"QueueUrl": runner.settings.sqs_standard_queue_url, "ReceiptHandle": "receipt-1"}]
    assert fake_db.completed[0] == job_id


def test_process_message_applies_exponential_backoff_for_retry(monkeypatch):
    fake_db = FakeDb()
    fake_sqs = FakeSqs()
    fake_s3 = FakeS3()
    job_id = uuid4()

    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(
        runner,
        "claim_job",
        lambda db, incoming_job_id: SimpleNamespace(job_id=incoming_job_id, priority=JobPriority.STANDARD),
    )
    monkeypatch.setattr(
        runner,
        "generate_result",
        lambda incoming_job_id, report_type, receive_count: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        runner,
        "mark_job_retryable_failure",
        lambda db, incoming_job_id, error_message, next_retry_at: setattr(
            fake_db, "retry", (incoming_job_id, error_message, next_retry_at)
        ),
    )
    monkeypatch.setattr(runner, "get_boto3_client", lambda service_name: fake_sqs if service_name == "sqs" else fake_s3)

    runner.process_message(runner.settings.sqs_standard_queue_url, build_message(job_id, receive_count=2), runner.WorkerState())

    assert fake_db.retry[0] == job_id
    assert fake_sqs.visibility_changes[0]["VisibilityTimeout"] == runner.compute_backoff_seconds(2)


def test_process_message_opens_circuit_breaker_after_threshold(monkeypatch):
    fake_db = FakeDb()
    fake_sqs = FakeSqs()
    fake_s3 = FakeS3()
    state = runner.WorkerState()
    job_id = uuid4()
    report_type = "fraud_alert"

    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(
        runner,
        "claim_job",
        lambda db, incoming_job_id: SimpleNamespace(job_id=incoming_job_id, priority=JobPriority.HIGH),
    )
    monkeypatch.setattr(
        runner,
        "generate_result",
        lambda incoming_job_id, report_type, receive_count: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        runner,
        "mark_job_retryable_failure",
        lambda db, incoming_job_id, error_message, next_retry_at: setattr(
            fake_db, "retry", (incoming_job_id, error_message, next_retry_at)
        ),
    )
    monkeypatch.setattr(runner, "get_boto3_client", lambda service_name: fake_sqs if service_name == "sqs" else fake_s3)

    for _ in range(runner.settings.worker_circuit_breaker_threshold):
        runner.process_message(runner.settings.sqs_high_priority_queue_url, build_message(job_id, report_type=report_type), state)

    assert runner.is_circuit_open(state, report_type, now=datetime.now(UTC))


def test_process_message_skips_when_circuit_is_open(monkeypatch):
    fake_db = FakeDb()
    fake_sqs = FakeSqs()
    fake_s3 = FakeS3()
    report_type = "fraud_alert"
    job_id = uuid4()
    state = runner.WorkerState(
        circuit_breakers={
            report_type: runner.CircuitBreakerEntry(
                consecutive_failures=runner.settings.worker_circuit_breaker_threshold,
                open_until=datetime.now(UTC) + timedelta(seconds=30),
            )
        }
    )

    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(runner, "get_boto3_client", lambda service_name: fake_sqs if service_name == "sqs" else fake_s3)

    runner.process_message(runner.settings.sqs_high_priority_queue_url, build_message(job_id, report_type=report_type), state)

    assert fake_sqs.visibility_changes
    assert not hasattr(fake_db, "retry")


def test_process_message_marks_failed_after_max_retries(monkeypatch):
    fake_db = FakeDb()
    fake_sqs = FakeSqs()
    fake_s3 = FakeS3()
    job_id = uuid4()

    monkeypatch.setattr(runner, "SessionLocal", lambda: fake_db)
    monkeypatch.setattr(
        runner,
        "claim_job",
        lambda db, incoming_job_id: SimpleNamespace(job_id=incoming_job_id, priority=JobPriority.STANDARD),
    )
    monkeypatch.setattr(
        runner,
        "generate_result",
        lambda incoming_job_id, report_type, receive_count: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        runner,
        "mark_job_failed",
        lambda db, incoming_job_id, error_message: setattr(fake_db, "failed", (incoming_job_id, error_message)),
    )
    monkeypatch.setattr(
        runner,
        "mark_job_retryable_failure",
        lambda db, incoming_job_id, error_message, next_retry_at: setattr(
            fake_db, "retry", (incoming_job_id, error_message, next_retry_at)
        ),
    )
    monkeypatch.setattr(runner, "get_boto3_client", lambda service_name: fake_sqs if service_name == "sqs" else fake_s3)

    runner.process_message(
        runner.settings.sqs_standard_queue_url,
        build_message(job_id, receive_count=runner.settings.worker_max_receive_count),
        runner.WorkerState(),
    )

    assert fake_db.failed[0] == job_id
    assert not hasattr(fake_db, "retry")
    assert fake_sqs.deleted


def test_report_simulation_service_retry_profile(monkeypatch):
    monkeypatch.setattr(report_simulation_service.time, "sleep", lambda seconds: None)

    try:
        report_simulation_service.simulate_report_processing("fraud_alert", 1)
    except report_simulation_service.SimulationError as exc:
        assert "Retry expected" in str(exc)
    else:
        raise AssertionError("Expected the first fraud_alert attempt to fail")

    payload = report_simulation_service.simulate_report_processing("fraud_alert", 2)

    assert payload["profile"] == "fraud_alert"
    assert payload["receive_count"] == 2
    assert payload["rows"]
