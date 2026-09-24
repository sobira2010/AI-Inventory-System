from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json
import logging
import os

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    # extra="ignore" so deployment-only env vars (e.g. PYTHON_VERSION on Render)
    # don't crash the app at import time
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = '["http://localhost:5173", "https://frolicking-daifuku-dc66bb.netlify.app"]'
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "nvidia/nemotron-3-super-120b-a12b:free"

    @property
    def database_url_resolved(self) -> str:
        """DATABASE_URL with deployment-friendly normalization applied.

        Neon (and some other providers) issue ``postgres://`` URLs; SQLAlchemy
        2.x only understands the ``postgresql://`` dialect name, so normalize
        the scheme instead of failing with "Can't load plugin
        sqlalchemy.dialects:postgres" at engine creation.
        """
        url = (self.DATABASE_URL or "").strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        return url

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS (JSON list or comma-separated string) into a list.

        Falls back to the known-good defaults rather than crashing the app at
        import time if the env var is malformed (a crash here would take down
        CORS for the whole app in production).
        """
        raw = (self.CORS_ORIGINS or "").strip()
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and all(isinstance(o, str) for o in parsed):
                origins = [o.strip() for o in parsed if o.strip()]
            else:
                raise ValueError("not a JSON string list")
        except (json.JSONDecodeError, ValueError):
            # Comma-separated form, e.g. set in the Render dashboard
            origins = [o.strip() for o in raw.split(",") if o.strip()]

        # Keep only plausible origins so malformed fragments never match a
        # real Origin header
        origins = [
            o for o in origins
            if o.startswith("http://") or o.startswith("https://")
        ]

        # Always guarantee localhost dev + the production frontend origin
        defaults = [
            "http://localhost:5173",
            "https://frolicking-daifuku-dc66bb.netlify.app",
        ]
        for origin in defaults:
            if origin not in origins:
                origins.append(origin)
        return origins


settings = Settings()


def _validate_production_database(s: Settings) -> None:
    """Fail fast on Render if the app is pointed at SQLite.

    A SQLite DATABASE_URL in production surfaces only at request time as a
    confusing "(sqlite3.OperationalError) no such table: users". Refuse to
    start instead, with an actionable message. Local development (where the
    RENDER env vars are absent) is unaffected and keeps working with SQLite.
    """
    on_render = bool(
        os.getenv("RENDER")
        or os.getenv("RENDER_SERVICE_ID")
        or os.getenv("RENDER_EXTERNAL_URL")
    )
    url = (s.database_url_resolved or "").lower()
    if on_render and (not url or url.startswith("sqlite")):
        raise RuntimeError(
            "Production misconfiguration: DATABASE_URL is a SQLite URL (or "
            "missing), so the app would run on SQLite in production. Set "
            "DATABASE_URL in the Render dashboard (Environment > Environment "
            "Variables) to the Neon PostgreSQL connection string "
            "(postgresql://...?sslmode=require) and redeploy. SQLite is not "
            "supported in production."
        )


_validate_production_database(settings)
