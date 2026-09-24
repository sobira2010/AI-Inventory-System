from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Bound TCP connection attempts so an unreachable database (e.g. a Neon
# network/VPC misconfiguration) fails in seconds instead of hanging for the
# OS-default ~2 minutes. SQLite dev URLs don't take connect_timeout.
_CONNECT_TIMEOUT_SECONDS = 10


def _engine_kwargs() -> dict:
    kwargs = dict(pool_pre_ping=True, pool_size=10, max_overflow=20)
    if not settings.database_url_resolved.startswith("sqlite"):
        kwargs["connect_args"] = {"connect_timeout": _CONNECT_TIMEOUT_SECONDS}
    return kwargs


engine = create_engine(
    # database_url_resolved normalizes postgres:// to postgresql:// (Neon)
    settings.database_url_resolved,
    **_engine_kwargs(),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    # On a cold start the schema init runs in a background thread (see
    # app.startup_db); wait briefly so the first requests don't race an
    # in-flight migration on a fresh database. Bounded: after the timeout the
    # request proceeds and any real database problem surfaces as-is.
    from app.startup_db import wait_for_schema

    wait_for_schema(timeout=10)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
