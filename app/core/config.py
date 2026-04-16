"""
config.py — Sports Diary API settings

pydantic-settings reads ALL values from the .env file automatically.
The Field(default=...) values are only used as a last resort when a key
is absent from BOTH the environment AND the .env file.
Nothing is hard-wired; every value is overridden by .env.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(
        extra="ignore",           # silently ignore unknown .env keys
        env_file=".env",          # load from .env in the working directory
        env_file_encoding="utf-8",
    )

    # ── JWT ───────────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(default="change-me")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # ── OTP ───────────────────────────────────────────────────────────────────
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 5
    OTP_SECRET_KEY: str = Field(default="change-me-otp")

    # ── MongoDB ───────────────────────────────────────────────────────────────
    # Value comes from .env: MONGODB_URL=mongodb+srv://...
    MONGODB_URL: str = Field(default="mongodb://localhost:27017")
    DATABASE_NAME: str = Field(default="sports_diary")

    # ── Security ──────────────────────────────────────────────────────────────
    ENCRYPTION_KEY: str = Field(default="change-me-enc")

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(default="*")

    # ── Email / SMTP ──────────────────────────────────────────────────────────
    SMTP_HOST: str = Field(default="")
    SMTP_PORT: int = Field(default=587)
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_FROM: str = Field(default="noreply@sportsdiary.app")

    # ── Business rules ────────────────────────────────────────────────────────
    PROFESSIONAL_FEE_INR: int = Field(default=3000)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def get_cors_origins(self) -> list:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


# Single shared instance — imported by every other module:
#   from app.core.config import settings
settings = Settings()