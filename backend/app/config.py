from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/horror"
    test_database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/horror_test"
    jwt_secret: str = "dev-only-secret-do-not-use-in-production-0123456789"
    jwt_expire_minutes: int = 60 * 24 * 14
    join_code: str = "dev-join-code"
    cors_origins: str = "http://localhost:5173"
    tmdb_api_key: str = ""

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _force_psycopg_driver(cls, v: str) -> str:
        # Neon / Render hand out plain postgresql:// URLs; SQLAlchemy needs the driver.
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
