from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.tables import JobPriority, JobStatus


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class JobCreatedResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    priority: JobPriority


class JobCreateRequest(BaseModel):
    report_type: str = Field(min_length=3, max_length=100)
    date_from: date
    date_to: date
    format: str = Field(pattern="^(csv|json|pdf)$")

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, value: date, info):
        date_from = info.data.get("date_from")
        if date_from and value < date_from:
            raise ValueError("date_to must be greater than or equal to date_from")
        return value


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    job_id: UUID
    user_id: UUID
    status: JobStatus
    priority: JobPriority
    report_type: str
    report_format: str
    date_from: date
    date_to: date
    created_at: datetime
    updated_at: datetime
    result_url: str | None = None
    error_message: str | None = None
    attempt_count: int
    next_retry_at: datetime | None = None


class JobListResponse(BaseModel):
    items: list[JobRead]
    page: int
    page_size: int
    total: int


class DependencyHealthRead(BaseModel):
    status: str
    detail: str


class JobRealtimeMessage(BaseModel):
    type: str
    jobs: list[JobRead]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    dependencies: dict[str, DependencyHealthRead]
