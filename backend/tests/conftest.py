import os
import sys
from collections.abc import Generator
from pathlib import Path
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/reports")
os.environ.setdefault("SQS_QUEUE_URL", "http://localhost:4566/000000000000/reports-jobs")
os.environ.setdefault("SQS_STANDARD_QUEUE_URL", "http://localhost:4566/000000000000/reports-jobs-standard")
os.environ.setdefault("SQS_HIGH_PRIORITY_QUEUE_URL", "http://localhost:4566/000000000000/reports-jobs-high")
os.environ.setdefault("SQS_DLQ_URL", "http://localhost:4566/000000000000/reports-jobs-dlq")
os.environ.setdefault("S3_REPORTS_BUCKET", "reports-results")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("APP_ENV", "test")

from app.main import app
from app.models.tables import User


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def fake_user() -> User:
    return User(
        id=UUID("4f85f452-e679-4ce8-90dd-e58f2057102a"),
        email="demo@example.com",
        password_hash="hashed",
    )
