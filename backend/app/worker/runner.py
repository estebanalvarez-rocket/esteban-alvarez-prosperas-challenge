import json
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.aws import get_boto3_client
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import configure_logging, get_logger
from app.models.tables import JobPriority
from app.services.job_service import (
    claim_job,
    mark_job_completed,
    mark_job_failed,
    mark_job_retryable_failure,
)
from app.services.metrics_service import publish_metric
from app.services.report_simulation_service import simulate_report_processing

settings = get_settings()
configure_logging()
logger = get_logger(__name__)


@dataclass
class CircuitBreakerEntry:
    consecutive_failures: int = 0
    open_until: datetime | None = None


@dataclass
class WorkerState:
    circuit_breakers: dict[str, CircuitBreakerEntry] = field(default_factory=dict)


def generate_result(job_id: str, report_type: str, receive_count: int) -> tuple[str, bytes]:
    payload = {
        "job_id": job_id,
        "generated_at": int(datetime.now(UTC).timestamp()),
        "report_type": report_type,
        **simulate_report_processing(report_type, receive_count),
    }
    return f"reports/{job_id}.json", json.dumps(payload, indent=2).encode("utf-8")


def get_circuit_breaker_entry(state: WorkerState, report_type: str) -> CircuitBreakerEntry:
    return state.circuit_breakers.setdefault(report_type, CircuitBreakerEntry())


def is_circuit_open(state: WorkerState, report_type: str, now: datetime | None = None) -> bool:
    current_time = now or datetime.now(UTC)
    entry = get_circuit_breaker_entry(state, report_type)
    if not entry.open_until:
        return False
    if current_time >= entry.open_until:
        entry.open_until = None
        entry.consecutive_failures = 0
        return False
    return True


def record_processing_success(state: WorkerState, report_type: str) -> None:
    entry = get_circuit_breaker_entry(state, report_type)
    entry.consecutive_failures = 0
    entry.open_until = None


def record_processing_failure(state: WorkerState, report_type: str) -> bool:
    entry = get_circuit_breaker_entry(state, report_type)
    entry.consecutive_failures += 1
    if entry.consecutive_failures >= settings.worker_circuit_breaker_threshold:
        entry.open_until = datetime.now(UTC) + timedelta(seconds=settings.worker_circuit_breaker_timeout_seconds)
        publish_metric("CircuitBreakerOpened", dimensions={"ReportType": report_type})
        logger.warning(
            "circuit_breaker_opened",
            extra={
                "extra_fields": {
                    "report_type": report_type,
                    "open_until": entry.open_until.isoformat(),
                    "consecutive_failures": entry.consecutive_failures,
                }
            },
        )
        return True
    return False


def compute_backoff_seconds(receive_count: int) -> int:
    delay = settings.worker_retry_base_delay_seconds * (2 ** max(receive_count - 1, 0))
    return min(delay, settings.worker_retry_max_delay_seconds)


def get_result_url(key: str) -> str:
    base_url = settings.s3_result_base_url or settings.aws_endpoint_url or f"https://{settings.s3_reports_bucket}.s3.amazonaws.com"
    return f"{base_url}/{key}"


def handle_open_circuit(queue_url: str, message: dict, report_type: str, sqs) -> None:
    sqs.change_message_visibility(
        QueueUrl=queue_url,
        ReceiptHandle=message["ReceiptHandle"],
        VisibilityTimeout=settings.worker_circuit_breaker_timeout_seconds,
    )
    logger.info(
        "job_skipped_circuit_open",
        extra={"extra_fields": {"job_id": json.loads(message["Body"])["job_id"], "report_type": report_type}},
    )


def process_message(queue_url: str, message: dict, state: WorkerState | None = None) -> None:
    worker_state = state or WorkerState()
    body = json.loads(message["Body"])
    receipt_handle = message["ReceiptHandle"]
    receive_count = int(message["Attributes"]["ApproximateReceiveCount"])
    job_id = UUID(body["job_id"])
    report_type = body.get("report_type", "unknown")

    db = SessionLocal()
    sqs = get_boto3_client("sqs")
    s3 = get_boto3_client("s3")

    try:
        if is_circuit_open(worker_state, report_type):
            handle_open_circuit(queue_url, message, report_type, sqs)
            return

        claimed = claim_job(db, job_id)
        if not claimed:
            logger.info("job_already_claimed", extra={"extra_fields": {"job_id": str(job_id)}})
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            return

        logger.info(
            "job_processing_started",
            extra={
                "extra_fields": {
                    "job_id": str(job_id),
                    "receive_count": receive_count,
                    "priority": claimed.priority.value,
                    "report_type": report_type,
                }
            },
        )
        key, content = generate_result(str(job_id), report_type, receive_count)
        s3.put_object(Bucket=settings.s3_reports_bucket, Key=key, Body=content, ContentType="application/json")

        result_url = get_result_url(key)
        mark_job_completed(db, job_id, result_url)
        record_processing_success(worker_state, report_type)
        logger.info("job_processing_completed", extra={"extra_fields": {"job_id": str(job_id), "result_url": result_url}})
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
    except Exception as exc:
        circuit_opened = record_processing_failure(worker_state, report_type)
        if receive_count >= settings.worker_max_receive_count:
            mark_job_failed(db, job_id, str(exc))
            logger.exception(
                "job_processing_failed_final",
                extra={"extra_fields": {"job_id": str(job_id), "receive_count": receive_count, "report_type": report_type}},
            )
            sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            return

        backoff_seconds = max(
            compute_backoff_seconds(receive_count),
            settings.worker_circuit_breaker_timeout_seconds if circuit_opened else 0,
        )
        next_retry_at = datetime.now(UTC) + timedelta(seconds=backoff_seconds)
        mark_job_retryable_failure(db, job_id, str(exc), next_retry_at)
        sqs.change_message_visibility(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle,
            VisibilityTimeout=backoff_seconds,
        )
        publish_metric("JobRetryDelaySeconds", value=backoff_seconds, unit="Seconds", dimensions={"ReportType": report_type})
        logger.exception(
            "job_processing_failed_retryable",
            extra={
                "extra_fields": {
                    "job_id": str(job_id),
                    "receive_count": receive_count,
                    "report_type": report_type,
                    "backoff_seconds": backoff_seconds,
                }
            },
        )
    finally:
        db.close()


def receive_messages(sqs, queue_url: str) -> list[dict]:
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=settings.worker_poll_seconds,
        AttributeNames=["ApproximateReceiveCount"],
    )
    return response.get("Messages", [])


def main() -> None:
    sqs = get_boto3_client("sqs")
    running: set[Future] = set()
    state = WorkerState()
    queue_order = [
        (settings.sqs_high_priority_queue_url, JobPriority.HIGH.value),
        (settings.sqs_standard_queue_url, JobPriority.STANDARD.value),
    ]
    seen_queue_urls: set[str] = set()
    unique_queue_order = []
    for queue_url, priority in queue_order:
        if queue_url in seen_queue_urls:
            continue
        seen_queue_urls.add(queue_url)
        unique_queue_order.append((queue_url, priority))

    with ThreadPoolExecutor(max_workers=settings.worker_concurrency) as executor:
        while True:
            if len(running) >= settings.worker_concurrency:
                done, running = wait(running, return_when=FIRST_COMPLETED)
                for future in done:
                    future.result()

            messages = []
            for queue_url, priority in unique_queue_order:
                messages = receive_messages(sqs, queue_url)
                if messages:
                    logger.info("worker_messages_received", extra={"extra_fields": {"priority": priority, "count": len(messages)}})
                    for message in messages:
                        running.add(executor.submit(process_message, queue_url, message, state))
                    break


if __name__ == "__main__":
    main()
