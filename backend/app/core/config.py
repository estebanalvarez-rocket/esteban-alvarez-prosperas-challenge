from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    app_name: str = "Reports Platform"
    app_env: str = "local"
    app_version: str = "0.1.0"
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    db_host: str | None = Field(default=None, alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str | None = Field(default=None, alias="DB_NAME")
    db_user: str | None = Field(default=None, alias="DB_USER")
    db_password: str | None = Field(default=None, alias="DB_PASSWORD")

    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_endpoint_url: str | None = Field(default=None, alias="AWS_ENDPOINT_URL")
    aws_access_key_id: str = Field(default="test", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="test", alias="AWS_SECRET_ACCESS_KEY")

    sqs_queue_url: str | None = Field(default=None, alias="SQS_QUEUE_URL")
    sqs_standard_queue_url: str | None = Field(default=None, alias="SQS_STANDARD_QUEUE_URL")
    sqs_high_priority_queue_url: str | None = Field(default=None, alias="SQS_HIGH_PRIORITY_QUEUE_URL")
    sqs_dlq_url: str = Field(alias="SQS_DLQ_URL")
    s3_reports_bucket: str = Field(alias="S3_REPORTS_BUCKET")
    s3_result_base_url: str | None = Field(default=None, alias="S3_RESULT_BASE_URL")
    cloudwatch_namespace: str = Field(default="ReportsPlatform", alias="CLOUDWATCH_NAMESPACE")

    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MINUTES")

    cors_origins_raw: str = Field(default="http://localhost:3000,http://127.0.0.1:3000", alias="CORS_ORIGINS")
    worker_concurrency: int = Field(default=2, alias="WORKER_CONCURRENCY")
    worker_poll_seconds: int = Field(default=20, alias="WORKER_POLL_SECONDS")
    worker_max_receive_count: int = Field(default=3, alias="WORKER_MAX_RECEIVE_COUNT")
    worker_sleep_min_seconds: int = Field(default=5, alias="WORKER_SLEEP_MIN_SECONDS")
    worker_sleep_max_seconds: int = Field(default=30, alias="WORKER_SLEEP_MAX_SECONDS")
    worker_circuit_breaker_threshold: int = Field(default=3, alias="WORKER_CIRCUIT_BREAKER_THRESHOLD")
    worker_circuit_breaker_timeout_seconds: int = Field(default=60, alias="WORKER_CIRCUIT_BREAKER_TIMEOUT_SECONDS")
    worker_retry_base_delay_seconds: int = Field(default=5, alias="WORKER_RETRY_BASE_DELAY_SECONDS")
    worker_retry_max_delay_seconds: int = Field(default=120, alias="WORKER_RETRY_MAX_DELAY_SECONDS")
    websocket_poll_interval_seconds: int = Field(default=2, alias="WEBSOCKET_POLL_INTERVAL_SECONDS")
    high_priority_report_types_raw: str = Field(
        default="fraud_alert,security_incident,executive_summary",
        alias="HIGH_PRIORITY_REPORT_TYPES",
    )

    @model_validator(mode="after")
    def build_database_url(self):
        if self.database_url:
            pass
        else:
            db_parts = [self.db_host, self.db_name, self.db_user, self.db_password]
            if all(db_parts):
                self.database_url = (
                    f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
                )
            else:
                raise ValueError("DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD must be configured")

        queue_url = self.sqs_standard_queue_url or self.sqs_queue_url
        if not queue_url:
            raise ValueError("SQS_STANDARD_QUEUE_URL or SQS_QUEUE_URL must be configured")
        self.sqs_standard_queue_url = queue_url
        self.sqs_high_priority_queue_url = self.sqs_high_priority_queue_url or queue_url
        return self

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def high_priority_report_types(self) -> set[str]:
        return {item.strip().lower() for item in self.high_priority_report_types_raw.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
