from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.schemas import (
    JobCreatedResponse,
    JobCreateRequest,
    JobListResponse,
    JobRead,
)
from app.models.tables import User
from app.services.job_service import create_job, get_job_for_user, list_jobs_for_user

router = APIRouter()


@router.post("", response_model=JobCreatedResponse, status_code=status.HTTP_201_CREATED)
def create_job_route(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobCreatedResponse:
    job = create_job(db, current_user, payload)
    return JobCreatedResponse(job_id=job.job_id, status=job.status, priority=job.priority)


@router.get("/{job_id}", response_model=JobRead)
def get_job_route(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobRead:
    job = get_job_for_user(db, job_id, current_user.id)
    return JobRead.model_validate(job)


@router.get("", response_model=JobListResponse)
def list_jobs_route(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JobListResponse:
    items, total = list_jobs_for_user(db, current_user.id, page, page_size)
    return JobListResponse(
        items=[JobRead.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )
