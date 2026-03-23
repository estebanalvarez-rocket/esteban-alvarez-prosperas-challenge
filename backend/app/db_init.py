from sqlalchemy import text

from app.core.database import Base, engine
from app.core.logging import configure_logging, get_logger
from app.models.tables import Job, User

configure_logging()
logger = get_logger(__name__)

SCHEMA_PATCHES = [
    """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
            CREATE TYPE job_status AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_priority') THEN
            CREATE TYPE job_priority AS ENUM ('HIGH', 'STANDARD');
        END IF;
    END $$;
    """,
    """
    ALTER TABLE IF EXISTS jobs
    ADD COLUMN IF NOT EXISTS priority job_priority NOT NULL DEFAULT 'STANDARD';
    """,
    """
    ALTER TABLE IF EXISTS jobs
    ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMPTZ NULL;
    """,
]


def init_db() -> None:
    _ = (Job, User)
    logger.info("db_init_started")
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        for statement in SCHEMA_PATCHES:
            connection.execute(text(statement))
    logger.info("db_init_completed")


if __name__ == "__main__":
    init_db()
