import boto3

from app.core.config import get_settings


def get_boto3_client(service_name: str):
    settings = get_settings()
    client_kwargs = {
        "region_name": settings.aws_region,
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
    }
    if settings.aws_endpoint_url:
        client_kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client(service_name, **client_kwargs)
