import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, get_logger, request_id_context
from app.db_init import init_db
from app.models.schemas import HealthResponse
from app.services.health_service import get_health_report

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def startup() -> None:
    if settings.app_env == "test":
        logger.info("skipping_db_init_for_tests")
        return
    init_db()


@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    token = request_id_context.set(request_id)
    logger.info(
        "incoming_request",
        extra={"extra_fields": {"path": request.url.path, "method": request.method}},
    )
    try:
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logger.info(
            "completed_request",
            extra={
                "extra_fields": {
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                }
            },
        )
        return response
    finally:
        request_id_context.reset(token)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def healthcheck() -> HealthResponse:
    return HealthResponse.model_validate(get_health_report())
