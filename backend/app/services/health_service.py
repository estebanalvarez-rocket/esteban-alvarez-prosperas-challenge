from dataclasses import dataclass

from sqlalchemy import text

from app.core.aws import get_boto3_client
from app.core.config import get_settings
from app.core.database import engine


@dataclass
class DependencyHealth:
    name: str
    status: str
    detail: str


def check_database() -> DependencyHealth:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return DependencyHealth(name="database", status="ok", detail="PostgreSQL reachable")
    except Exception as exc:
        return DependencyHealth(name="database", status="error", detail=str(exc))


def check_sqs() -> DependencyHealth:
    settings = get_settings()
    try:
        sqs = get_boto3_client("sqs")
        sqs.get_queue_attributes(QueueUrl=settings.sqs_high_priority_queue_url, AttributeNames=["QueueArn"])
        sqs.get_queue_attributes(QueueUrl=settings.sqs_standard_queue_url, AttributeNames=["QueueArn"])
        sqs.get_queue_attributes(QueueUrl=settings.sqs_dlq_url, AttributeNames=["QueueArn"])
        return DependencyHealth(name="sqs", status="ok", detail="Priority queues and DLQ reachable")
    except Exception as exc:
        return DependencyHealth(name="sqs", status="error", detail=str(exc))


def check_s3() -> DependencyHealth:
    settings = get_settings()
    try:
        s3 = get_boto3_client("s3")
        s3.head_bucket(Bucket=settings.s3_reports_bucket)
        return DependencyHealth(name="s3", status="ok", detail="Bucket reachable")
    except Exception as exc:
        return DependencyHealth(name="s3", status="error", detail=str(exc))


def check_cloudwatch() -> DependencyHealth:
    settings = get_settings()
    try:
        cloudwatch = get_boto3_client("cloudwatch")
        cloudwatch.list_metrics(Namespace=settings.cloudwatch_namespace, MaxRecords=1)
        return DependencyHealth(name="cloudwatch", status="ok", detail="CloudWatch reachable")
    except Exception as exc:
        return DependencyHealth(name="cloudwatch", status="error", detail=str(exc))


def get_health_report() -> dict:
    dependencies = [check_database(), check_sqs(), check_s3(), check_cloudwatch()]
    overall_status = "ok" if all(item.status == "ok" for item in dependencies) else "degraded"
    settings = get_settings()
    return {
        "status": overall_status,
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "dependencies": {
            item.name: {
                "status": item.status,
                "detail": item.detail,
            }
            for item in dependencies
        },
    }
