import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_SQLITE_PATH = (_BACKEND_DIR / "civicfix.db").as_posix()
def validate_and_resolve_database_url(
    raw_url: str | None = None,
    environment: str | None = None
) -> tuple[str, dict]:
    """
    Validates and resolves the database URL and engine kwargs.
    In production (ENVIRONMENT=production), DATABASE_URL is strictly required
    and must be a PostgreSQL connection string. SQLite, missing, or empty values fail fast.
    Connection string values are never echoed in error messages or logs to prevent secret leakage.
    """
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "")
    is_production = environment.strip().lower() == "production"

    if raw_url is None:
        raw_url = os.getenv("DATABASE_URL")

    cleaned_url = (raw_url or "").strip()

    if is_production:
        if not cleaned_url:
            raise RuntimeError(
                "Production database configuration error: DATABASE_URL environment variable is missing or empty. "
                "A persistent PostgreSQL database URL is required in production."
            )
        # Normalize legacy postgres:// prefix
        if cleaned_url.startswith("postgres://"):
            cleaned_url = cleaned_url.replace("postgres://", "postgresql://", 1)

        if cleaned_url.startswith("sqlite"):
            raise RuntimeError(
                "Production database configuration error: SQLite is not permitted in production. "
                "A persistent PostgreSQL database URL (e.g. Supabase Session Pooler) is required to prevent data loss."
            )
        if not cleaned_url.startswith("postgresql://") and not cleaned_url.startswith("postgresql+"):
            raise RuntimeError(
                "Production database configuration error: DATABASE_URL must be a valid PostgreSQL connection string "
                "(beginning with 'postgresql://')."
            )
    else:
        # Development mode default
        if not cleaned_url:
            cleaned_url = f"sqlite:///{_DEFAULT_SQLITE_PATH}"
        elif cleaned_url.startswith("postgres://"):
            cleaned_url = cleaned_url.replace("postgres://", "postgresql://", 1)

    connect_args = {}
    engine_kwargs = {"pool_pre_ping": True}

    if cleaned_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        engine_kwargs["connect_args"] = connect_args
    else:
        # PostgreSQL settings: recycle idle connections after 300s
        engine_kwargs["pool_recycle"] = 300

    return cleaned_url, engine_kwargs

DATABASE_URL, engine_kwargs = validate_and_resolve_database_url()

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
