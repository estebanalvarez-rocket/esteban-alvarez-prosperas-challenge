import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.auth import decode_token
from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models.schemas import JobRead, JobRealtimeMessage
from app.models.tables import User
from app.services.job_service import list_latest_jobs_for_user

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


def build_jobs_payload(user_id: UUID) -> JobRealtimeMessage:
    db = SessionLocal()
    try:
        jobs = list_latest_jobs_for_user(db, user_id)
        return JobRealtimeMessage(type="jobs.snapshot", jobs=[JobRead.model_validate(job) for job in jobs])
    finally:
        db.close()


def resolve_user(token: str) -> User | None:
    payload = decode_token(token)
    db = SessionLocal()
    try:
        return db.get(User, payload["sub"])
    finally:
        db.close()


@router.websocket("/jobs")
async def jobs_websocket(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401, reason="Missing token")
        return

    try:
        user = resolve_user(token)
    except Exception:
        await websocket.close(code=4401, reason="Invalid token")
        return

    if not user:
        await websocket.close(code=4401, reason="Unknown user")
        return

    await websocket.accept()
    last_snapshot = ""

    try:
        while True:
            payload = build_jobs_payload(user.id)
            serialized = payload.model_dump_json()
            if serialized != last_snapshot:
                await websocket.send_text(serialized)
                last_snapshot = serialized
            await asyncio.sleep(settings.websocket_poll_interval_seconds)
    except WebSocketDisconnect:
        logger.info("jobs_websocket_disconnected", extra={"extra_fields": {"user_id": str(user.id)}})
    except Exception:
        logger.exception("jobs_websocket_failed", extra={"extra_fields": {"user_id": str(user.id)}})
        await websocket.close(code=1011, reason="Realtime channel failed")
