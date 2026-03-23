import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.aws import get_boto3_client
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.logging import get_logger
from app.models.schemas import JobCreateRequest
from app.models.tables import Job, JobPriority, JobStatus, User
from app.services.metrics_service import publish_metric

settings = get_settings()
logger = get_logger(__name__)


def get_job_priority(report_type: str) -> JobPriority:
    if report_type.lower() in settings.high_priority_report_types:
        return JobPriority.HIGH
    return JobPriority.STANDARD


def get_queue_url(priority: JobPriority) -> str:
    if priority == JobPriority.HIGH:
        return settings.sqs_high_priority_queue_url
    return settings.sqs_standard_queue_url


def create_job(db: Session, current_user: User, payload: JobCreateRequest) -> Job:
    priority = get_job_priority(payload.report_type)
    job = Job(
        user_id=current_user.id,
        status=JobStatus.PENDING,
        priority=priority,
        report_type=payload.report_type,
        report_format=payload.format,
        date_from=payload.date_from,
        date_to=payload.date_to,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    sqs = get_boto3_client("sqs")
    queue_url = get_queue_url(priority)
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(
            {
                "job_id": str(job.job_id),
                "user_id": str(current_user.id),
                "report_type": payload.report_type,
                "priority": priority.value,
                "requested_at": datetime.now(UTC).isoformat(),
            }
        ),
    )
    publish_metric(
        "JobsCreated",
        dimensions={"Priority": priority.value, "ReportType": payload.report_type},
    )
    logger.info(
        "job_created",
        extra={
            "extra_fields": {
                "job_id": str(job.job_id),
                "user_id": str(current_user.id),
                "status": job.status.value,
                "priority": priority.value,
                "report_type": job.report_type,
                "queue_url": queue_url,
            }
        },
    )

    return job


def get_job_for_user(db: Session, job_id: str, user_id: UUID) -> Job:
    job = db.scalar(select(Job).where(Job.job_id == UUID(job_id), Job.user_id == user_id))
    if not job:
        raise AppError("Job not found", 404)
    return job


def list_jobs_for_user(db: Session, user_id: UUID, page: int, page_size: int) -> tuple[list[Job], int]:
    offset = (page - 1) * page_size
    items = list(
        db.scalars(
            select(Job)
            .where(Job.user_id == user_id)
            .order_by(Job.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
    )
    total = db.scalar(select(func.count()).select_from(Job).where(Job.user_id == user_id)) or 0
    return items, total


def list_latest_jobs_for_user(db: Session, user_id: UUID, limit: int = 20) -> list[Job]:
    return list(
        db.scalars(
            select(Job)
            .where(Job.user_id == user_id)
            .order_by(Job.updated_at.desc(), Job.created_at.desc())
            .limit(limit)
        )
    )


def claim_job(db: Session, job_id: UUID) -> Job | None:
    statement = (
        update(Job)
        .where(Job.job_id == job_id, Job.status == JobStatus.PENDING)
        .values(
            status=JobStatus.PROCESSING,
            updated_at=datetime.now(UTC),
            attempt_count=Job.attempt_count + 1,
            next_retry_at=None,
        )
        .returning(Job)
    )
    claimed = db.execute(statement).scalar_one_or_none()
    db.commit()
    return claimed


def mark_job_completed(db: Session, job_id: UUID, result_url: str) -> None:
    db_job = db.get(Job, job_id)
    db.execute(
        update(Job)
        .where(Job.job_id == job_id)
        .values(
            status=JobStatus.COMPLETED,
            result_url=result_url,
            error_message=None,
            updated_at=datetime.now(UTC),
            next_retry_at=None,
        )
    )
    db.commit()
    if db_job:
        publish_metric(
            "JobsCompleted",
            dimensions={"Priority": db_job.priority.value, "ReportType": db_job.report_type},
        )


def mark_job_retryable_failure(db: Session, job_id: UUID, error_message: str, next_retry_at: datetime) -> None:
    db_job = db.get(Job, job_id)
    db.execute(
        update(Job)
        .where(Job.job_id == job_id)
        .values(
            status=JobStatus.PENDING,
            error_message=error_message[:500],
            last_error_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            next_retry_at=next_retry_at,
        )
    )
    db.commit()
    if db_job:
        publish_metric(
            "JobsRetried",
            dimensions={"Priority": db_job.priority.value, "ReportType": db_job.report_type},
        )


def mark_job_failed(db: Session, job_id: UUID, error_message: str) -> None:
    db_job = db.get(Job, job_id)
    db.execute(
        update(Job)
        .where(Job.job_id == job_id)
        .values(
            status=JobStatus.FAILED,
            error_message=error_message[:500],
            last_error_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            next_retry_at=None,
        )
    )
    db.commit()
    if db_job:
        publish_metric(
            "JobsFailed",
            dimensions={"Priority": db_job.priority.value, "ReportType": db_job.report_type},
        )
