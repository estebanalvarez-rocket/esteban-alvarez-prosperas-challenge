from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.errors import AppError
from app.models.tables import User

security = HTTPBearer()
settings = get_settings()


def encode_token(payload: dict) -> str:
    payload = payload.copy()
    payload["exp"] = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise AppError("Invalid authentication token", status.HTTP_401_UNAUTHORIZED) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    user = db.get(User, payload["sub"])
    if not user:
        raise AppError("Authenticated user no longer exists", status.HTTP_401_UNAUTHORIZED)
    return user
