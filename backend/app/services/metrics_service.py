from app.core.aws import get_boto3_client
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


def publish_metric(name: str, value: float = 1, unit: str = "Count", dimensions: dict[str, str] | None = None) -> None:
    metric_dimensions = [{"Name": key, "Value": value} for key, value in (dimensions or {}).items()]
    try:
        cloudwatch = get_boto3_client("cloudwatch")
        cloudwatch.put_metric_data(
            Namespace=settings.cloudwatch_namespace,
            MetricData=[
                {
                    "MetricName": name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": metric_dimensions,
                }
            ],
        )
    except Exception:
        logger.exception(
            "cloudwatch_metric_publish_failed",
            extra={"extra_fields": {"metric_name": name, "dimensions": dimensions or {}}},
        )
