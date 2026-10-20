import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DEFAULT_SQLITE_PATH = (_BACKEND_DIR / "civicfix.db").as_posix()
def normalize_postgres_driver_url(url: str) -> str:
    """
    Normalizes plain PostgreSQL URL schemes to use the installed psycopg2 driver
    (postgresql+psycopg2://) for compatibility with SQLAlchemy 2.x.
    Preserves existing driver-qualified schemes (e.g. postgresql+psycopg2://, postgresql+asyncpg://),
    all user credentials, hostnames, paths, and query parameters.
    Does not perform blind substring replacements.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def validate_and_resolve_database_url(
    raw_url: str | None = None,
    environment: str | None = None
) -> tuple[str, dict]:
    """
    Validates and resolves the database URL and engine kwargs.
    In production (ENVIRONMENT=production), DATABASE_URL is strictly required
    and must be a PostgreSQL connection string. SQLite, missing, or empty values fail fast.
    Plain 'postgres://' or 'postgresql://' URLs are safely normalized to 'postgresql+psycopg2://'
    to ensure SQLAlchemy 2.x routes to the installed psycopg2 driver while preserving query
    parameters, SSL configuration, and existing driver-qualified schemes.
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

        if cleaned_url.startswith("sqlite"):
            raise RuntimeError(
                "Production database configuration error: SQLite is not permitted in production. "
                "A persistent PostgreSQL database URL (e.g. Supabase Session Pooler) is required to prevent data loss."
            )

        if not cleaned_url.startswith("postgres://") and not cleaned_url.startswith("postgresql://") and not cleaned_url.startswith("postgresql+"):
            raise RuntimeError(
                "Production database configuration error: DATABASE_URL must be a valid PostgreSQL connection string "
                "(beginning with 'postgresql://' or 'postgresql+')."
            )

        # Safely normalize plain scheme to psycopg2 driver without blind string replacement
        cleaned_url = normalize_postgres_driver_url(cleaned_url)
    else:
        # Development mode default
        if not cleaned_url:
            cleaned_url = f"sqlite:///{_DEFAULT_SQLITE_PATH}"
        elif cleaned_url.startswith("postgres://") or cleaned_url.startswith("postgresql://"):
            cleaned_url = normalize_postgres_driver_url(cleaned_url)

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
