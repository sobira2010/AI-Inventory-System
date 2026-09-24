"""Database schema initialization — non-blocking, bounded, idempotent.

Why this module exists and why it is architected this way:

Render runs ``uvicorn app.main:app --host 0.0.0.0 --port $PORT`` and then
scans for an open port. The server must bind 0.0.0.0:$PORT quickly or Render
kills the deploy with "Port scan timeout reached, no open ports detected".

Earlier revisions ran Alembic synchronously inside the FastAPI startup hook,
so the port was only bound AFTER Neon answered — a slow or unreachable Neon
(SYN blackhole, wrong host, VPC misconfiguration) stalled the bind for
minutes and the deploy timed out even though the code was fine.

The architecture now is:

* ``ensure_schema_async()`` (called from the FastAPI lifespan) spawns a
  daemon thread and returns immediately → uvicorn binds and serves
  right away, and Render's port scan always succeeds.
* The background worker runs the project's existing Alembic migrations
  (backend/alembic/versions/001_initial.py): idempotent, create-only,
  never drops tables or data, and bounded by a TCP connect timeout so a
  bad database fails in seconds instead of hanging forever.
* ``wait_for_schema()`` lets request handlers (app.database.get_db) avoid
  racing the init on cold start; it is bounded and never hangs requests.
* SQLite dev URLs skip Alembic entirely — local development behaves as
  before. Production (Render) remains PostgreSQL-only; that guard lives in
  app.config and is unchanged.

Secrets are never logged: only the URL scheme is printed.
"""

import logging
import os
import threading

from alembic import command
from alembic.config import Config

from app.config import settings

logger = logging.getLogger(__name__)

# Bounded failure: libpq defaults to an OS-level (~2 min) TCP timeout, and an
# unreachable host would stall the migration worker for minutes. 10s is ample
# for a healthy Neon TCP handshake anywhere in the world.
_CONNECT_TIMEOUT_SECONDS = 10

# Resolve the migrations directory from this file's location so the startup
# hook works regardless of the process working directory (Render, Docker,
# systemd units, etc. may all start uvicorn from different cwd's).
_ALEMBIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "alembic"
)

# Set once the schema-init attempt has settled (success OR failure), so
# request handlers never race it and never wait on a dead worker.
_settled = threading.Event()


def _with_connect_timeout(db_url: str) -> str:
    """Add libpq connect_timeout to a PostgreSQL URL (user's value wins)."""
    if db_url.startswith("sqlite") or "connect_timeout" in db_url:
        return db_url
    sep = "&" if "?" in db_url else "?"
    return f"{db_url}{sep}connect_timeout={_CONNECT_TIMEOUT_SECONDS}"


def _make_config(db_url: str) -> Config:
    """Build an Alembic Config pointing at the project's migrations.

    Percent signs are escaped for configparser interpolation (passwords can
    contain them). script_location is an absolute path (see _ALEMBIC_DIR),
    so this works no matter the process working directory.
    """
    cfg = Config()
    cfg.set_main_option("script_location", _ALEMBIC_DIR)
    cfg.set_main_option("sqlalchemy.url", db_url.replace("%", "%%"))
    return cfg


def _run_migrations_blocking() -> None:
    """Bring the database up to head revision. Blocking; call from a worker."""
    db_url = settings.database_url_resolved
    scheme = db_url.split("://", 1)[0] if "://" in db_url else "(no scheme)"

    if db_url.startswith("sqlite"):
        logger.info(
            "Skipping Alembic schema init for SQLite (local development as before)"
        )
        return

    logger.info("Running Alembic migrations on database with scheme=%s ...", scheme)
    command.upgrade(_make_config(_with_connect_timeout(db_url)), "head")
    logger.info("Database schema is up to date (alembic revision: head)")


def ensure_schema_async() -> None:
    """Kick off schema init in a daemon thread. Returns immediately.

    Called from the FastAPI lifespan so the server binds 0.0.0.0:$PORT at
    once — database problems can delay migrations, never the port bind.
    A failed init is logged and swallowed here; requests then surface the
    real database error and /health keeps answering for Render's scanner.
    """
    def _worker() -> None:
        try:
            _run_migrations_blocking()
        except Exception:
            logger.exception(
                "Database schema initialization failed; API keeps serving and "
                "database errors will surface per-request"
            )
        finally:
            _settled.set()

    threading.Thread(target=_worker, name="db-schema-init", daemon=True).start()


def wait_for_schema(timeout: float = 10.0) -> bool:
    """Wait (bounded) until the schema-init attempt has settled.

    Returns True once settled (init succeeded or failed), False on timeout.
    Used by app.database.get_db so the very first requests on a cold start
    don't race an in-flight migration on a fresh database.
    """
    return _settled.wait(timeout)
