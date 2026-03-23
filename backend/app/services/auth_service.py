from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import encode_token
from app.core.errors import AppError
from app.models.schemas import UserRegister
from app.models.tables import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_user(db: Session, payload: UserRegister) -> User:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise AppError("Email already registered", 409)

    user = User(email=payload.email.lower(), password_hash=pwd_context.hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if not user or not pwd_context.verify(password, user.password_hash):
        raise AppError("Invalid email or password", 401)
    return user


def create_access_token(user: User) -> str:
    return encode_token({"sub": str(user.id), "email": user.email})
