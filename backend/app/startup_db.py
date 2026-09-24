"""Database schema initialization at application startup.

Render runs only ``uvicorn app.main:app`` — there is no pre-deploy step and
no shell access, so ``alembic upgrade head`` would otherwise never run against
the production database and a fresh Neon instance would have no tables
("(sqlite3|psycopg2).OperationalError: no such table: users" on login).

This module runs the project's existing Alembic migrations (backend/
alembic/versions/001_initial.py) programmatically at startup:

* Idempotent: Alembic creates the ``alembic_version`` bookkeeping table and
  only applies migrations that have not run yet.
* Non-destructive: it never drops tables or data. 001_initial uses
  ``op.create_table`` only; on an already-migrated database it is a no-op.
* Local development is unaffected: with a SQLite URL the app keeps using the
  existing database file as before, so we skip Alembic there — running
  001_initial against an existing legacy SQLite file would fail on existing
  tables, and changing dev behavior is out of scope for this fix.

Secrets are never logged: only the URL scheme is printed.
"""

import logging

from alembic import command
from alembic.config import Config

from app.config import settings

logger = logging.getLogger(__name__)

_ALEMBIC_DIR = "alembic"


def _make_config(db_url: str) -> Config:
    """Build an Alembic Config pointing at the project's migrations.

    Percent signs are escaped for configparser interpolation (passwords can
    contain them). The working directory is the backend/ root at startup, so
    the relative script_location resolves to backend/alembic.
    """
    cfg = Config()
    cfg.set_main_option("script_location", _ALEMBIC_DIR)
    cfg.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))
    return cfg


def run_migrations() -> None:
    """Bring the target database up to the latest Alembic revision (idempotent)."""
    db_url = settings.database_url_resolved
    scheme = db_url.split("://", 1)[0] if "://" in db_url else "(no scheme)"

    if db_url.startswith("sqlite"):
        logger.info(
            "Skipping Alembic schema init for SQLite (local development as before)"
        )
        return

    logger.info("Running Alembic migrations on database with scheme=%s ...", scheme)
    command.upgrade(_make_config(db_url), "head")
    logger.info("Database schema is up to date (alembic revision: head)")
