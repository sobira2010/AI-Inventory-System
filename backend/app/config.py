from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json
import logging

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
